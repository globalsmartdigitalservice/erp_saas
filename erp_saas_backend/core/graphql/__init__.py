"""Piezas de GraphQL compartidas por todos los módulos."""

from .errores import EnmascararErrores, SchemaDelErp, es_esperado
from .paginacion import InfoDePagina, Pagina

__all__ = [
    "Pagina",
    "InfoDePagina",
    "SchemaDelErp",
    "EnmascararErrores",
    "es_esperado",
]
