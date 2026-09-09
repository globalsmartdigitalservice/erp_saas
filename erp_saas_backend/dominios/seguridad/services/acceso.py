import datetime

from django.utils import timezone

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ESTADO_ACTIVO,
    NOMBRE_EXCEPCION_BLOQUEO,
    NOMBRE_EXCEPCION_PERMISO,
)
from dominios.seguridad.repository import acceso as repo


class Veredicto:
    """La respuesta, con el MOTIVO adentro. No es un booleano a propósito:
    "no podés entrar" sin decir por qué obliga a revisar tres tablas a mano.

     `motivo` es para el registro y para quien administra, no
    necesariamente para la pantalla de login."""

    def __init__(self, permitido: bool, motivo: str = ""):
        self.permitido = permitido
        self.motivo = motivo

    def __bool__(self):
        return self.permitido

    def __repr__(self):
        return f"<Veredicto {'SÍ' if self.permitido else 'NO'}: {self.motivo}>"


def _estado_activo():
    return tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
    )


def _dentro_del_tramo(
    hora: datetime.time, desde: datetime.time, hasta: datetime.time
) -> bool:
    """¿La hora cae en el tramo?

     El caso que se olvida siempre: `hasta` MENOR que `desde` significa que
    el tramo cruza la medianoche (22:00 → 06:00). Sin esto el turno noche no
    deja entrar NUNCA: ninguna hora está a la vez después de las 22 y antes
    de las 6."""
    if desde <= hasta:
        return desde <= hora <= hasta
    return hora >= desde or hora <= hasta


def _hay_horario(membresia_id: int, momento: datetime.datetime) -> bool:
    activo = _estado_activo()
    if activo is None:
        return False

    horarios = repo.horarios_vigentes(
        membresia_id, momento.date(), activo.pk
    )
    if not horarios:
        # SIN HORARIOS CARGADOS SE PUEDE ENTRAR SIEMPRE, y es a
        # propósito: la mayoría de las empresas no va a usar esta función.
        # Si "sin horario" significara "nunca", activar el módulo dejaría
        # a todos afuera de golpe.
        return True

    del_dia = [h for h in horarios if h.dia_semana == momento.weekday()]

    # Y los del día ANTERIOR que cruzan la medianoche: a la 1 de la
    # mañana del martes, quien manda es el turno del lunes 22:00–06:00.
    ayer = (momento.weekday() - 1) % 7
    del_dia += [
        h for h in horarios if h.dia_semana == ayer and h.cruza_medianoche
    ]

    if not del_dia:
        return False

    hora = momento.time()
    return any(_dentro_del_tramo(hora, h.hora_inicio, h.hora_fin) for h in del_dia)


def _excepcion_del_dia(membresia_id: int, momento: datetime.datetime):
    """Devuelve ("BLOQUEO"|"PERMISO", excepcion) o (None, None). Si hay
    varias el mismo día, BLOQUEO gana."""
    activo = _estado_activo()
    if activo is None:
        return None, None

    excepciones = repo.excepciones_del_dia(membresia_id, momento.date(), activo.pk)
    if not excepciones:
        return None, None

    hora = momento.time()
    aplicables = [
        e
        for e in excepciones
        if e.es_dia_completo or _dentro_del_tramo(hora, e.hora_inicio, e.hora_fin)
    ]
    if not aplicables:
        return None, None

    # Se compara contra el TEXTO de la fila, no contra un id: si la
    # tipología se renombra desde el panel del proveedor deja de coincidir,
    # y un BLOQUEO deja de bloquear sin error ni log. BLOQUEO se evalúa
    # primero a propósito — gana sobre PERMISO, que hace lo contrario.
    for excepcion in aplicables:
        if excepcion.tipo.nombre == NOMBRE_EXCEPCION_BLOQUEO:
            return NOMBRE_EXCEPCION_BLOQUEO, excepcion

    for excepcion in aplicables:
        if excepcion.tipo.nombre == NOMBRE_EXCEPCION_PERMISO:
            return NOMBRE_EXCEPCION_PERMISO, excepcion

    return None, None


def puede_entrar(
    *,
    membresia_id: int,
    momento: datetime.datetime | None = None,
    mac: str | None = None,
    ip_publica: str | None = None,
) -> Veredicto:
    """El veredicto completo.

    `mac` la manda el cliente instalado; desde un navegador no se puede leer.
    Si llega `None` la comprobación del equipo NO se hace: exigir el cliente
    antes de que exista dejaría a todos afuera."""
    # `localtime()` y no `datetime.now()`: aquel devuelve la hora de
    # TIME_ZONE y este la del servidor, que dentro del contenedor es UTC.
    # Los horarios se cargan en hora local, así que con `now()` un turno de
    # 08:00 a 17:00 dejaba entrar de 04:00 a 13:00, sin error ninguno.
    momento = momento or timezone.localtime()

    tipo, excepcion = _excepcion_del_dia(membresia_id, momento)

    if tipo == NOMBRE_EXCEPCION_BLOQUEO:
        return Veredicto(
            False,
            f"Bloqueado el {excepcion.fecha}"
            + (f": {excepcion.motivo}" if excepcion.motivo else ""),
        )

    # El PERMISO saltea el horario, que es para lo que existe: "vino el
    # domingo a cerrar el inventario".
    if tipo != NOMBRE_EXCEPCION_PERMISO and not _hay_horario(membresia_id, momento):
        return Veredicto(
            False,
            f"Fuera del horario permitido ({momento:%A %H:%M}).",
        )

    if mac is not None:
        veredicto = _verificar_equipo(membresia_id, mac, ip_publica, momento)
        if not veredicto:
            return veredicto

    return Veredicto(True, "")


def _verificar_equipo(
    membresia_id: int, mac: str, ip_publica: str | None, momento
) -> Veredicto:
    """MAC exacta + IP registrada. La MAC sola no alcanza porque se puede
    copiar en otro equipo, pero desde afuera de la oficina la IP no coincide.
    Las dos juntas cubren los dos casos."""
    activo = _estado_activo()
    if activo is None:
        return Veredicto(False, "Falta el estado ACTIVO en las tipologías.")

    autorizacion = repo.autorizacion_vigente_por_mac(
        membresia_id, mac, momento.date(), activo.pk
    )
    if autorizacion is None:
        # El mensaje NO dice si el equipo existe y no está autorizado, o
        # si no existe: quien prueba MACs no tiene que poder averiguar
        # cuáles están dadas de alta.
        return Veredicto(False, "Este equipo no está autorizado para esta persona.")

    registrada = autorizacion.dispositivo.ip
    if registrada and ip_publica and str(registrada) != str(ip_publica):
        return Veredicto(
            False,
            "El equipo está autorizado pero se está conectando desde otra red.",
        )

    return Veredicto(True, "")


__all__ = ["puede_entrar", "Veredicto"]
