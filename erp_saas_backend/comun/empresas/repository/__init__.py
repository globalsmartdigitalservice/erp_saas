"""
Acceso a datos. Consulta y escribe, nada más.

NO valida invariantes ni decide nada: eso vive en `services/`.
"""

from . import empresa, empresa_moneda, empresa_pais

__all__ = ["empresa", "empresa_pais", "empresa_moneda"]
