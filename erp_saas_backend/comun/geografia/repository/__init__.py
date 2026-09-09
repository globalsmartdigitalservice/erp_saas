"""
Acceso a datos. Consulta y escribe, nada más.

NO valida invariantes ni decide nada: eso vive en `services/`. Si acá
aparece un `if` de negocio, está en el lugar equivocado.
"""

from . import pais, ubicacion

__all__ = ["pais", "ubicacion"]
