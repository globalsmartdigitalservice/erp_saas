"""
El idioma activo de la request.

Uso:

    from core.idioma import idioma_actual

 ESTE PAQUETE NO ES UNA APP DE DJANGO y no tiene modelos. El catálogo
de idiomas y las traducciones viven en `comun/idiomas/` (CAPA 2); acá
solo está la cajita del contexto, que es CAPA 1 y no depende de nada.

Es la misma división que ya existe entre `core/tenancy/` (el mecanismo)
y `comun/empresas/` (la tabla).
"""

from .contexto import (
    establecer_idioma,
    hay_idioma,
    idioma,
    idioma_actual,
    restaurar_idioma,
)

__all__ = [
    "idioma",
    "idioma_actual",
    "hay_idioma",
    "establecer_idioma",
    "restaurar_idioma",
]
