"""Cómo ve el frontend una lista paginada."""

from typing import Generic, TypeVar

import strawberry

from core.paginacion import Pagina as PaginaDeDominio

T = TypeVar("T")


@strawberry.type(name="InfoDePagina")
class InfoDePagina:
    """
    Lo que la pantalla necesita para dibujar el paginador.

    `total` es el de ESTA empresa, no el del sistema: el conteo va sobre
    el queryset que el manager ya filtró.
    """

    total: int
    limite: int
    desde: int
    hay_siguiente: bool

    @classmethod
    def desde_pagina(cls, pagina: PaginaDeDominio) -> "InfoDePagina":
        return cls(
            total=pagina.total,
            limite=pagina.limite,
            desde=pagina.desde,
            hay_siguiente=pagina.hay_siguiente,
        )


@strawberry.type
class Pagina(Generic[T]):
    """
    Un pedazo de una lista larga.

    Devuelve `items` + `info` en vez de una lista suelta porque sin el
    total la pantalla no puede mostrar "página 3 de 20" ni saber si hay
    una siguiente.
    """

    items: list[T]
    info: InfoDePagina


__all__ = ["Pagina", "InfoDePagina"]
