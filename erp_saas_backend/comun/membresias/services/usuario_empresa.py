import datetime

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas import api as empresas
from comun.membresias.models import UsuarioEmpresa
from comun.membresias.repository import usuario_empresa as repo
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from comun.usuarios import api as usuarios
from comun.usuarios.models import Usuario
from core.tenancy import empresa_actual


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado de membresía"
    )


def _persona_del_cliente(usuario_id: int) -> Usuario:
    """La persona, si es del cliente de la sesión.

    El orden importa: quién es dueño de esa cuenta se comprueba ANTES que
    cualquier otra cosa. Validando primero el estado, el mensaje "el usuario
    'jperez' está dado de baja" entregaba el nombre de alguien de otro
    cliente a quien probara ids."""
    usuario = usuarios.obtener_usuario_del_cliente(usuario_id)

    if not usuario.is_active:
        raise ValidationError(
            f"El usuario '{usuario.username}' está dado de baja del sistema. "
            f"Reactívelo antes de afiliarlo a una empresa."
        )
    return usuario



EMPRESA_NO_DISPONIBLE = "Esa empresa no está disponible."


def _empresa_de_la_sesion() -> int:
    """Dónde se afilia: la empresa donde está parado quien llama.

    No se recibe por parámetro. Mientras venía de afuera había que comprobar
    que la cuenta y la empresa fueran del mismo cliente, y esa comprobación no
    podía saber cuál de los dos era el ajeno: los dos los mandaba quien
    llamaba. Saliendo de la sesión, las dos pertenencias quedan garantizadas
    por construcción."""
    empresa_id = empresa_actual()
    if empresa_id is None:
        raise ValidationError(
            "No hay empresa en la sesión: no se sabe a cuál afiliar."
        )
    return empresa_id


def _validar_fechas(fecha_asignacion, fecha_finalizacion) -> None:
    if fecha_finalizacion is None:
        return
    if fecha_finalizacion < fecha_asignacion:
        raise ValidationError(
            "La fecha de finalización no puede ser anterior a la de asignación."
        )


@transaction.atomic
def afiliar(
    *,
    usuario_id: int,
    fecha_asignacion: datetime.date | None = None,
    estado_id: int,
) -> UsuarioEmpresa:
    """Da de alta a una persona en la empresa de la sesión."""
    empresa_id = _empresa_de_la_sesion()
    _validar_estado(estado_id)
    usuario = _persona_del_cliente(usuario_id)

    if repo.existe_en(usuario_id, empresa_id):
        raise ValidationError(
            f"'{usuario.username}' ya está dado de alta en esa empresa. "
            f"Si se había ido y volvió, reactive su membresía en vez de "
            f"crear otra: así el historial queda en un solo lugar."
        )

    return repo.crear_en(
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        # Por defecto hoy: la fecha en que se lo dio de alta.
        fecha_asignacion=fecha_asignacion or datetime.date.today(),
        estado_id=estado_id,
    )


@transaction.atomic
def afiliar_al_grupo(
    *,
    usuario_id: int,
    fecha_asignacion: datetime.date | None = None,
    estado_id: int,
) -> list[UsuarioEmpresa]:
    """
    Da de alta a una persona en una empresa Y EN TODAS SUS SUCURSALES.

    Devuelve solo las membresías CREADAS. Las empresas del grupo donde
    la persona ya estaba se saltean en silencio, no dan error: el caso
    real es el gerente que ya estaba en dos sucursales y al que hay que
    sumarle la tercera. Si esto fallara, el administrador tendría que
    afiliar de a una para averiguar cuál faltaba.

     Es `atomic`: o entran todas las que faltaban o no entra ninguna.
    Un alta a medias dejaría al gerente con acceso a la mitad del grupo
    y nadie se daría cuenta hasta que reclame.
    """
    empresa_id = _empresa_de_la_sesion()
    _validar_estado(estado_id)
    usuario = _persona_del_cliente(usuario_id)

    grupo = empresas.descendientes_de(empresa_id)
    if not grupo:
        raise ValidationError(EMPRESA_NO_DISPONIBLE)

    fecha = fecha_asignacion or datetime.date.today()
    creadas = []

    for empresa in grupo:
        if repo.existe_en(usuario_id, empresa.pk):
            continue
        creadas.append(
            repo.crear_en(
                usuario_id=usuario_id,
                empresa_id=empresa.pk,
                fecha_asignacion=fecha,
                estado_id=estado_id,
            )
        )

    return creadas


@transaction.atomic
def desafiliar(
    *,
    membresia_id: int,
    estado_baja_id: int,
    fecha_finalizacion: datetime.date | None = None,
) -> UsuarioEmpresa:
    """
    Saca a una persona de una empresa. Soft delete: cambia el estado y
    pone la fecha de fin, no borra la fila.

    La persona sigue existiendo y sus otras empresas no se tocan.
    """
    _validar_estado(estado_baja_id)

    membresia = repo.obtener(membresia_id)
    if membresia is None:
        raise ValidationError(f"No existe la membresía {membresia_id}.")

    fecha = fecha_finalizacion or datetime.date.today()
    _validar_fechas(membresia.fecha_asignacion, fecha)

    membresia.estado_id = estado_baja_id
    membresia.fecha_finalizacion = fecha
    membresia.save(update_fields=["estado", "fecha_finalizacion"])
    return membresia


@transaction.atomic
def reactivar(*, membresia_id: int, estado_activo_id: int) -> UsuarioEmpresa:
    """
    El que se fue y volvió. Se reactiva su fila en vez de crear otra
    —lo impide el `unique(usuario, empresa)`— y así el historial queda
    en un solo lugar.
    """
    _validar_estado(estado_activo_id)

    membresia = repo.obtener(membresia_id)
    if membresia is None:
        raise ValidationError(f"No existe la membresía {membresia_id}.")

    membresia.estado_id = estado_activo_id
    membresia.fecha_finalizacion = None
    membresia.save(update_fields=["estado", "fecha_finalizacion"])
    return membresia
