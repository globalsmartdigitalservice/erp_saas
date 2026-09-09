import datetime
import re

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ESTADO_BAJA,
)
from dominios.seguridad.models import Dispositivo
from dominios.seguridad.repository import acceso as repo

# 00:1B:44:11:3A:B7 o 00-1b-44-11-3a-b7. Se valida la FORMA, no que la
# placa exista: eso no se puede saber desde el servidor.
_MAC = re.compile(r"^[0-9A-F]{2}([:-][0-9A-F]{2}){5}$")


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )


def _normalizar_mac(mac: str) -> str:
    """
    En mayúsculas y con `:`. Sin esto, `00:1b:44:...` y `00-1B-44-...` son
    la misma placa y entrarían como dos equipos — y peor, al comparar en
    el ingreso ninguna coincidiría con la guardada.
    """
    return (mac or "").strip().upper().replace("-", ":")


def _validar_mac(mac: str, excluir_id: int | None = None) -> None:
    if not mac:
        return  # Vacía es válida: todavía no la reportó el cliente instalado.
    if not _MAC.match(mac):
        raise ValidationError(
            f"'{mac}' no tiene forma de dirección MAC. Se esperan seis pares "
            f"hexadecimales, como '00:1B:44:11:3A:B7'."
        )
    if repo.existe_mac(mac, excluir_id):
        raise ValidationError(f"Ya hay un equipo registrado con la MAC '{mac}'.")


def _resolver_membresia(membresia_id: int):
    membresia = membresias.obtener_membresia(membresia_id)
    if membresia is None:
        raise ValidationError(
            f"La membresía {membresia_id} no está disponible para esta empresa."
        )
    return membresia


def _resolver_dispositivo(dispositivo_id: int) -> Dispositivo:
    """
    El agujero que el mecanismo no tapa. Va SIEMPRE por el manager.

    El mensaje es el mismo exista o no el id: si dijera "no existe"
   para uno y "no podés" para otro, probando ids se averigua qué equipos
   hay en la base de otros clientes.
   """
    dispositivo = Dispositivo.objects.filter(pk=dispositivo_id).first()
    if dispositivo is None:
        raise ValidationError(
            f"El dispositivo {dispositivo_id} no está disponible para esta empresa."
        )
    return dispositivo


def _tipologia_de_baja():
    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Corré: python manage.py cargar_semillas"
        )
    return baja


@transaction.atomic
def registrar_dispositivo(
    *,
    nombre: str,
    tipo_id: int,
    estado_id: int,
    mac: str = "",
    ip: str | None = None,
    identificador: str = "",
) -> Dispositivo:
    """
    Da de alta un equipo EN LA EMPRESA ACTIVA. `empresa` no se recibe: la
    pone `ModeloTenant.save()` desde el contexto.
    """
    _validar_estado(estado_id)
    tipologias.exigir_del_agrupador(
        tipo_id, AGRUPADOR.TIPO_DISPOSITIVO, "tipo de dispositivo"
    )

    mac = _normalizar_mac(mac)
    _validar_mac(mac)

    if not (nombre or "").strip():
        raise ValidationError("El equipo necesita un nombre para reconocerlo.")

    return repo.crear_dispositivo(
        nombre=nombre.strip(),
        tipo_id=tipo_id,
        mac=mac,
        ip=ip,
        identificador=identificador,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar_dispositivo(
    dispositivo_id: int,
    *,
    nombre: str | None = None,
    mac: str | None = None,
    ip: str | None = None,
    identificador: str | None = None,
    estado_id: int | None = None,
) -> Dispositivo:
    dispositivo = _resolver_dispositivo(dispositivo_id)

    if estado_id is not None:
        _validar_estado(estado_id)

    if mac is not None:
        mac = _normalizar_mac(mac)
        _validar_mac(mac, excluir_id=dispositivo_id)

    campos = {
        campo: valor
        for campo, valor in (
            ("nombre", nombre),
            ("mac", mac),
            ("ip", ip),
            ("identificador", identificador),
            ("estado_id", estado_id),
        )
        if valor is not None
    }
    if not campos:
        return dispositivo

    return repo.actualizar_dispositivo(dispositivo, **campos)


@transaction.atomic
def autorizar_dispositivo(
    *,
    membresia_id: int,
    dispositivo_id: int,
    estado_id: int,
    fecha_inicio: datetime.date | None = None,
    fecha_fin: datetime.date | None = None,
    autorizado_por_id: int | None = None,
):
    _validar_estado(estado_id)
    _resolver_membresia(membresia_id)
    _resolver_dispositivo(dispositivo_id)

    fecha_inicio = fecha_inicio or datetime.date.today()
    if fecha_fin is not None and fecha_fin < fecha_inicio:
        raise ValidationError(
            "La fecha de fin no puede ser anterior a la de inicio."
        )

    if repo.hay_autorizacion_vigente(membresia_id, dispositivo_id):
        raise ValidationError(
            "Esa persona ya tiene ese equipo autorizado. Si querés cambiarle "
            "las fechas, editá la autorización en vez de crear otra."
        )

    return repo.crear_autorizacion(
        usuario_empresa_id=membresia_id,
        dispositivo_id=dispositivo_id,
        estado_id=estado_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        autorizado_por_id=autorizado_por_id,
    )


@transaction.atomic
def desautorizar_dispositivo(
    *, autorizacion_id: int, fecha_fin: datetime.date | None = None
):
    """Le pone fecha de fin y la da de baja. NO borra: es historial."""
    autorizacion = repo.obtener_autorizacion(autorizacion_id)
    if autorizacion is None:
        raise ValidationError(f"No existe la autorización {autorizacion_id}.")

    fecha_fin = fecha_fin or datetime.date.today()
    if fecha_fin < autorizacion.fecha_inicio:
        raise ValidationError(
            "La fecha de fin no puede ser anterior a la de inicio."
        )

    return repo.actualizar_autorizacion(
        autorizacion, fecha_fin=fecha_fin, estado_id=_tipologia_de_baja().pk
    )


@transaction.atomic
def cargar_horario(
    *,
    membresia_id: int,
    dia_semana: int,
    hora_inicio: datetime.time,
    hora_fin: datetime.time,
    estado_id: int,
    vigencia_desde: datetime.date | None = None,
    vigencia_hasta: datetime.date | None = None,
):
    """
     `hora_fin` MENOR que `hora_inicio` es VÁLIDO: es el turno que cruza
    la medianoche (22:00 → 06:00). Rechazarlo dejaría afuera al turno
    noche, que existe en cualquier farmacia de guardia.

    Lo que sí se rechaza es que sean IGUALES: un tramo de duración cero no
    deja entrar nunca, y quien lo carga cree que sí.
    """
    _validar_estado(estado_id)
    _resolver_membresia(membresia_id)

    if not 0 <= dia_semana <= 6:
        raise ValidationError(
            "El día de la semana va de 0 (lunes) a 6 (domingo)."
        )

    if hora_inicio == hora_fin:
        raise ValidationError(
            "La hora de inicio y la de fin no pueden ser la misma: sería un "
            "tramo de duración cero y no dejaría entrar nunca."
        )

    vigencia_desde = vigencia_desde or datetime.date.today()
    if vigencia_hasta is not None and vigencia_hasta < vigencia_desde:
        raise ValidationError(
            "El fin de la vigencia no puede ser anterior a su inicio."
        )

    if repo.hay_horario_igual(membresia_id, dia_semana, hora_inicio, hora_fin):
        raise ValidationError("Esa persona ya tiene cargado ese mismo tramo.")

    return repo.crear_horario(
        usuario_empresa_id=membresia_id,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        vigencia_desde=vigencia_desde,
        vigencia_hasta=vigencia_hasta,
        estado_id=estado_id,
    )


@transaction.atomic
def quitar_horario(*, horario_id: int):
    horario = repo.obtener_horario(horario_id)
    if horario is None:
        raise ValidationError(f"No existe el horario {horario_id}.")

    return repo.actualizar_horario(horario, estado_id=_tipologia_de_baja().pk)


@transaction.atomic
def cargar_excepcion(
    *,
    membresia_id: int,
    fecha: datetime.date,
    tipo_id: int,
    estado_id: int,
    hora_inicio: datetime.time | None = None,
    hora_fin: datetime.time | None = None,
    motivo: str = "",
    creado_por_id: int | None = None,
):
    """
    Un día suelto que no sigue el horario de siempre.

    `tipo` decide si DEJA ENTRAR (PERMISO) o IMPIDE ENTRAR (BLOQUEO), o
    sea lo contrario una de la otra — por eso se valida su agrupador con
    tanto cuidado como el estado.
    """
    _validar_estado(estado_id)
    _resolver_membresia(membresia_id)

    # De este campo depende que la excepción DEJE ENTRAR o IMPIDA ENTRAR,
    # así que se valida con el mismo cuidado que el estado.
    tipologias.exigir_del_agrupador(
        tipo_id, AGRUPADOR.TIPO_EXCEPCION_HORARIO, "tipo de excepción (PERMISO o BLOQUEO)"
    )

    if (hora_inicio is None) != (hora_fin is None):
        raise ValidationError(
            "O van las dos horas o ninguna. Con una sola no se puede saber si "
            "el resto del día entra o no."
        )

    if hora_inicio is not None and hora_inicio == hora_fin:
        raise ValidationError(
            "La hora de inicio y la de fin no pueden ser la misma."
        )

    return repo.crear_excepcion(
        usuario_empresa_id=membresia_id,
        fecha=fecha,
        tipo_id=tipo_id,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        motivo=motivo,
        creado_por_id=creado_por_id,
        estado_id=estado_id,
    )


@transaction.atomic
def quitar_excepcion(*, excepcion_id: int):
    excepcion = repo.obtener_excepcion(excepcion_id)
    if excepcion is None:
        raise ValidationError(f"No existe la excepción {excepcion_id}.")

    return repo.actualizar_excepcion(
        excepcion, estado_id=_tipologia_de_baja().pk
    )
