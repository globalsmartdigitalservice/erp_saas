"""Lo que el frontend manda para armar y asignar roles."""

import datetime

import strawberry


@strawberry.input(name="CrearRolInput")
class CrearRolInput:
    """
    `empresa_id` NO está y no va a estar: el rol se crea SIEMPRE en la
    empresa activa, que sale del contexto del servidor. Si viniera de
    afuera, alguien podría crear un rol dentro de otra empresa mandando
    un id.
    """

    nombre: str
    estado_id: strawberry.ID


@strawberry.input(name="ActualizarRolInput")
class ActualizarRolInput:
    nombre: str | None = None
    estado_id: strawberry.ID | None = None


@strawberry.input(name="AsignarRolInput")
class AsignarRolInput:
    membresia_id: strawberry.ID
    rol_id: strawberry.ID
    estado_id: strawberry.ID
    fecha_inicio: datetime.date | None = None
    fecha_fin: datetime.date | None = None
    motivo: str = ""
