"""Las consultas de geografía."""

import strawberry

from comun.geografia import api as geografia
from comun.tipologias import api as tipologias
from comun.tipologias.graphql.types import TipologiaType

from .types import PaisType, UbicacionGeograficaType


def _resolver_estados(filas):
    """
    Trae de una sola consulta el estado de todas las filas.

    Este es el batch a mano del que depende no tener N+1: se juntan
    todos los `estado_id` y se piden juntos por el `api.py` de
    tipologias. Sin esto, 400 ubicaciones = 401 consultas.
    """
    estados = tipologias.obtener_varias({f.estado_id for f in filas})
    return {
        id_: TipologiaType.desde_modelo(tipologia)
        for id_, tipologia in estados.items()
    }


@strawberry.type
class PaisQueries:
    @strawberry.field(description="Todos los países.")
    def paises(self) -> list[PaisType]:
        filas = geografia.listar_paises()
        estados = _resolver_estados(filas)
        return [PaisType.desde_modelo(p, estados.get(p.estado_id)) for p in filas]

    @strawberry.field(description="Un país por su id.")
    def pais(self, id: strawberry.ID) -> PaisType | None:
        fila = geografia.obtener_pais(int(id))
        if fila is None:
            return None
        estados = _resolver_estados([fila])
        return PaisType.desde_modelo(fila, estados.get(fila.estado_id))


@strawberry.type
class UbicacionQueries:
    @strawberry.field(description="Todas las ubicaciones de un país.")
    def ubicaciones(self, pais_id: strawberry.ID) -> list[UbicacionGeograficaType]:
        filas = geografia.listar_ubicaciones_de_pais(int(pais_id))
        estados = _resolver_estados(filas)
        return [
            UbicacionGeograficaType.desde_modelo(u, estados.get(u.estado_id))
            for u in filas
        ]

    @strawberry.field(
        description="Las divisiones de primer nivel de un país (los departamentos)."
    )
    def divisiones_raiz(self, pais_id: strawberry.ID) -> list[UbicacionGeograficaType]:
        filas = geografia.listar_raices(int(pais_id))
        estados = _resolver_estados(filas)
        return [
            UbicacionGeograficaType.desde_modelo(u, estados.get(u.estado_id))
            for u in filas
        ]

    @strawberry.field(
        description="Las divisiones hijas DIRECTAS de una ubicación. "
        "Para toda la descendencia hace falta una consulta recursiva, "
        "todavía no implementada."
    )
    def divisiones(self, ubicacion_id: strawberry.ID) -> list[UbicacionGeograficaType]:
        filas = geografia.hijos_de(int(ubicacion_id))
        estados = _resolver_estados(filas)
        return [
            UbicacionGeograficaType.desde_modelo(u, estados.get(u.estado_id))
            for u in filas
        ]


@strawberry.type
class GeografiaQuery(PaisQueries, UbicacionQueries):
    """La superficie de consulta de geografía. Solo compone."""
