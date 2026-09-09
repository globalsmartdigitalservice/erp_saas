"""Lo que el frontend manda para afiliar o dar de baja."""

import datetime

import strawberry


@strawberry.input(name="AfiliarInput")
class AfiliarInput:
    usuario_id: strawberry.ID
    empresa_id: strawberry.ID
    estado_id: strawberry.ID
    fecha_asignacion: datetime.date | None = None


@strawberry.input(name="DesafiliarInput")
class DesafiliarInput:
    membresia_id: strawberry.ID
    estado_baja_id: strawberry.ID
    fecha_finalizacion: datetime.date | None = None
