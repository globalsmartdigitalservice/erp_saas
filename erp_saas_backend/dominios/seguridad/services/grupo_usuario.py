import datetime

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ESTADO_ACTIVO,
    NOMBRE_ESTADO_BAJA,
)
from dominios.seguridad.models import GrupoEmpresa, GrupoUsuario
from dominios.seguridad.repository import grupo_usuario as repo


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )


def _resolver_rol_asignable(grupo_id: int) -> GrupoEmpresa:
    """
    El invariante 3. Va SIEMPRE por el manager, nunca por id crudo.

     El mensaje es el mismo exista o no el id: si dijera "no existe" para
    uno y "no podés" para otro, quien prueba ids averigua cuáles existen
    en la base de otros clientes. Misma política que el módulo 04.
    """
    grupo = GrupoEmpresa.objects.filter(pk=grupo_id).first()
    if grupo is None:
        raise ValidationError(
            f"El rol {grupo_id} no está disponible para esta empresa."
        )
    return grupo


def _resolver_membresia(membresia_id: int):
    """
    Va por el api de `membresias`, que filtra por la empresa del contexto:
    una membresía de otra empresa simplemente no aparece.
    """
    membresia = membresias.obtener_membresia(membresia_id)
    if membresia is None:
        raise ValidationError(
            f"La membresía {membresia_id} no está disponible para esta empresa."
        )
    return membresia


def _validar_fechas(fecha_inicio, fecha_fin) -> None:
    if fecha_fin is not None and fecha_fin < fecha_inicio:
        raise ValidationError(
            "La fecha de fin no puede ser anterior a la de inicio."
        )


@transaction.atomic
def asignar(
    *,
    membresia_id: int,
    grupo_id: int,
    estado_id: int,
    fecha_inicio: datetime.date | None = None,
    fecha_fin: datetime.date | None = None,
    asignado_por_id: int | None = None,
    motivo: str = "",
) -> GrupoUsuario:
    """
    Le da un rol a una persona dentro de esta empresa.

    El rol puede ser de la casa matriz: es justamente lo que permite
    definir "Cajero" una sola vez arriba y usarlo en las 20 sucursales.
    """
    _validar_estado(estado_id)
    _resolver_membresia(membresia_id)
    _resolver_rol_asignable(grupo_id)

    fecha_inicio = fecha_inicio or datetime.date.today()
    _validar_fechas(fecha_inicio, fecha_fin)

    if repo.hay_asignacion_vigente(membresia_id, grupo_id):
        raise ValidationError(
            "Esa persona ya tiene ese rol vigente. Si querés cambiarle las "
            "fechas o el motivo, editá la asignación en vez de crear otra."
        )

    return repo.crear(
        usuario_empresa_id=membresia_id,
        grupo_empresa_id=grupo_id,
        estado_id=estado_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        asignado_por_id=asignado_por_id,
        motivo=motivo,
    )


@transaction.atomic
def quitar(
    *, asignacion_id: int, fecha_fin: datetime.date | None = None
) -> GrupoUsuario:
    """
    Le saca el rol a una persona: le pone fecha de fin y la da de baja.

    NO se borra la fila. Esta tabla es historial: "¿quién le dio permiso
    de anular a Juan, y hasta cuándo?" es una pregunta de auditoría que
    se contesta con estas filas.
    """
    asignacion = repo.obtener(asignacion_id)
    if asignacion is None:
        raise ValidationError(f"No existe la asignación {asignacion_id}.")

    fecha_fin = fecha_fin or datetime.date.today()
    _validar_fechas(asignacion.fecha_inicio, fecha_fin)

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Corré: python manage.py cargar_semillas"
        )

    return repo.actualizar(asignacion, fecha_fin=fecha_fin, estado_id=baja.pk)


@transaction.atomic
def actualizar(
    asignacion_id: int,
    *,
    fecha_fin: datetime.date | None = None,
    motivo: str | None = None,
    estado_id: int | None = None,
) -> GrupoUsuario:
    """
    Cambia las fechas o el motivo.

     NO deja cambiar ni la persona ni el rol: eso no es editar, es otra
    asignación. Si se pudiera, el historial diría que Juan tuvo un rol
    que en realidad nunca tuvo.
    """
    asignacion = repo.obtener(asignacion_id)
    if asignacion is None:
        raise ValidationError(f"No existe la asignación {asignacion_id}.")

    if estado_id is not None:
        _validar_estado(estado_id)

    if fecha_fin is not None:
        _validar_fechas(asignacion.fecha_inicio, fecha_fin)

    campos = {
        campo: valor
        for campo, valor in (
            ("fecha_fin", fecha_fin),
            ("motivo", motivo),
            ("estado_id", estado_id),
        )
        if valor is not None
    }
    if not campos:
        return asignacion

    return repo.actualizar(asignacion, **campos)


def permisos_vigentes_de(membresia_id: int) -> set[str]:
    """
    Los códigos de permiso que esa persona tiene HOY en esta empresa.

    Es lo que va a consumir el backend de autenticación,
    para que `user.has_perm()` diga la verdad. Se devuelve el `codename`
    con su app —`"ventas.anular_factura"`—, que es el formato que espera
    Django.

     DOS CONSULTAS, no una por rol: primero los roles vigentes, después
    los permisos de todos ellos juntos. Sin eso, cada verificación de
    permiso costaría una consulta por rol de la persona.
    """
    from dominios.seguridad.repository import grupo_empresa as repo_grupo

    activo = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
    )
    if activo is None:
        return set()

    roles = repo.roles_vigentes_de(membresia_id, activo.pk)
    if not roles:
        return set()

    lineas = repo_grupo.listar_permisos_de_varios([r.grupo_empresa_id for r in roles])
    return {
        f"{linea.auth_permission.content_type.app_label}."
        f"{linea.auth_permission.codename}"
        for linea in lineas
    }
