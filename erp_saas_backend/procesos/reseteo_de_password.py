"""El administrador le devuelve el acceso a alguien de su empresa.

Se llega a la persona por su MEMBRESÍA: el encargado de una sucursal resetea
a los de su sucursal, no a cualquier cuenta del cliente.
"""

import dataclasses

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.membresias import api as membresias
from comun.usuarios import api as usuarios
from dominios.seguridad import api as seguridad


@dataclasses.dataclass(frozen=True)
class Reseteo:
    usuario_id: int
    username: str
    password: str


@transaction.atomic
def resetear(*, membresia_id: int, password: str | None = None) -> Reseteo:
    """Devuelve la contraseña en claro: es la única vez que se puede leer.

    Cierra TODAS las sesiones de la cuenta, sin excepción. Un reseteo se pide
    porque algo pasó, y la contraseña es de la cuenta, así que la persona
    también queda afuera de las otras empresas donde trabaje."""
    membresia = membresias.obtener_membresia(membresia_id)
    if membresia is None:
        raise ValidationError(f"No existe la membresía {membresia_id}.")

    usuario, en_claro = usuarios.resetear_password(membresia.usuario_id, password)
    seguridad.cerrar_sesiones_de(usuario.pk)

    return Reseteo(usuario_id=usuario.pk, username=usuario.username, password=en_claro)


__all__ = ["resetear", "Reseteo"]
