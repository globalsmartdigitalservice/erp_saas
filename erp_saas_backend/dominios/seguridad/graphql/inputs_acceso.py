"""Lo que el frontend manda para equipos y horarios."""

import datetime

import strawberry


@strawberry.input(name="RegistrarDispositivoInput")
class RegistrarDispositivoInput:
    """`empresa_id` no está: sale del contexto del servidor."""

    nombre: str
    tipo_id: strawberry.ID
    estado_id: strawberry.ID
    mac: str = ""
    ip: str | None = None
    identificador: str = ""


@strawberry.input(name="AutorizarDispositivoInput")
class AutorizarDispositivoInput:
    membresia_id: strawberry.ID
    dispositivo_id: strawberry.ID
    estado_id: strawberry.ID
    fecha_inicio: datetime.date | None = None
    fecha_fin: datetime.date | None = None


@strawberry.input(name="CargarHorarioInput")
class CargarHorarioInput:
    """
     `hora_fin` MENOR que `hora_inicio` es válido: turno que cruza la
    medianoche (22:00 → 06:00). No lo rechaces en el frontend.

    `dia_semana`: 0 = lunes … 6 = domingo (convención de Python).
    """

    membresia_id: strawberry.ID
    dia_semana: int
    hora_inicio: datetime.time
    hora_fin: datetime.time
    estado_id: strawberry.ID
    vigencia_desde: datetime.date | None = None
    vigencia_hasta: datetime.date | None = None


@strawberry.input(name="CargarExcepcionInput")
class CargarExcepcionInput:
    """
    `tipo_id` decide si DEJA ENTRAR (PERMISO) o IMPIDE ENTRAR (BLOQUEO).

    Las horas: o las dos o ninguna. Sin ellas es una excepción de día
    completo.
    """

    membresia_id: strawberry.ID
    fecha: datetime.date
    tipo_id: strawberry.ID
    estado_id: strawberry.ID
    hora_inicio: datetime.time | None = None
    hora_fin: datetime.time | None = None
    motivo: str = ""
