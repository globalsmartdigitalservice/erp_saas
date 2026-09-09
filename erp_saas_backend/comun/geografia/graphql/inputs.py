"""Los inputs de las mutations."""

import strawberry


@strawberry.input
class CrearPaisInput:
    cod_pais: str
    nombre: str
    codigo_iso: str
    estado_id: strawberry.ID


@strawberry.input
class ActualizarPaisInput:
    cod_pais: str | None = None
    nombre: str | None = None
    codigo_iso: str | None = None
    estado_id: strawberry.ID | None = None


@strawberry.input
class CrearUbicacionInput:
    pais_id: strawberry.ID
    nombre: str
    tipo: str
    estado_id: strawberry.ID
    division_superior_id: strawberry.ID | None = None
    codigo: str = ""

