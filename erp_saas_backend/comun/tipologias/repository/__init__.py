"""
Acceso a datos. Consulta y escribe, nada más.

NO valida invariantes ni decide nada: eso vive en `services/`.
"""

from . import empresa_agrupador, tipologia, tipologia_oculta

__all__ = ["tipologia", "empresa_agrupador", "tipologia_oculta"]
