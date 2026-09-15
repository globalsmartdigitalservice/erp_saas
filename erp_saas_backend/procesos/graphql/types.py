"""Lo que devuelven las mutations de los procesos."""

import strawberry

from comun.membresias.graphql.types import MembresiaType


@strawberry.type(name="AltaDeMiembro")
class AltaDeMiembroType:
    """`passwordTemporal` viene solo si la generó el sistema: es la única vez que se puede leer."""

    membresia: MembresiaType
    password_temporal: str | None
