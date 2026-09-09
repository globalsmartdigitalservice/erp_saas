"""Las consultas del árbol de pantallas: el menú y el armado de roles."""

import strawberry

from comun.catalogo_modulos import api as modulos

from .types import FuncionalidadType, SubModuloType


def _armar_arbol(pantallas) -> list[SubModuloType]:
    """Las pantallas con sus acciones en DOS consultas: se juntan los ids
    de pantalla y se piden todas las acciones de una vez."""
    acciones = modulos.listar_funcionalidades_de_varios([p.pk for p in pantallas])

    por_pantalla: dict[int, list[FuncionalidadType]] = {}
    for accion in acciones:
        por_pantalla.setdefault(accion.sub_modulo_id, []).append(
            FuncionalidadType.desde_modelo(accion)
        )

    return [
        SubModuloType.desde_modelo(p, por_pantalla.get(p.pk, [])) for p in pantallas
    ]


@strawberry.type
class CatalogoModulosQueries:
    @strawberry.field(
        description=(
            "Todas las pantallas del sistema con sus acciones. Es el árbol "
            "que se usa para armar un rol."
        )
    )
    def sub_modulos(self, estado_id: strawberry.ID | None = None) -> list[SubModuloType]:
        pantallas = modulos.listar_sub_modulos(
            int(estado_id) if estado_id is not None else None
        )
        return _armar_arbol(pantallas)

    @strawberry.field(
        description=(
            "Las pantallas de varios módulos, en una sola consulta. Es lo que "
            "arma el menú del cliente a partir de lo que tiene contratado."
        )
    )
    def sub_modulos_de(
        self, modulo_ids: list[strawberry.ID], estado_id: strawberry.ID | None = None
    ) -> list[SubModuloType]:
        pantallas = modulos.listar_sub_modulos_de_varios(
            [int(i) for i in modulo_ids],
            int(estado_id) if estado_id is not None else None,
        )
        return _armar_arbol(pantallas)

    @strawberry.field(description="Una pantalla por su código estable.")
    def sub_modulo_por_codigo(self, codigo: str) -> SubModuloType | None:
        pantalla = modulos.obtener_sub_modulo_por_codigo(codigo)
        if pantalla is None:
            return None
        return _armar_arbol([pantalla])[0]


@strawberry.type
class CatalogoModulosQuery(CatalogoModulosQueries):
    pass
