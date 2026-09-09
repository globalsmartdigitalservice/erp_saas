"""Las consultas de empresas."""

import strawberry

from comun.empresas import api as empresas
from comun.tipologias import api as tipologias
from comun.tipologias.graphql.types import TipologiaType

from .types import EmpresaMonedaType, EmpresaPaisType, EmpresaType


def _armar(filas):
    """
    Resuelve las TRES tipologías de todas las empresas en UNA consulta.

    Cada empresa tiene tipo, rubro y estado apuntando a `tipologia`. Sin
    este batch, 100 empresas serían 301 consultas.
    """
    ids = set()
    for e in filas:
        ids.update((e.tipo_empresa_id, e.rubro_id, e.estado_id))

    crudas = tipologias.obtener_varias(ids)
    tipos = {i: TipologiaType.desde_modelo(t) for i, t in crudas.items()}

    return [
        EmpresaType.desde_modelo(
            e,
            tipo_empresa=tipos.get(e.tipo_empresa_id),
            rubro=tipos.get(e.rubro_id),
            estado=tipos.get(e.estado_id),
        )
        for e in filas
    ]


@strawberry.type
class EmpresaQueries:
    @strawberry.field(description="Todas las empresas del sistema.")
    def empresas(self) -> list[EmpresaType]:
        return _armar(empresas.listar_empresas())

    @strawberry.field(
        description="Las casas matriz: las que no dependen de ninguna otra. "
        "Un cliente del SaaS = una matriz."
    )
    def matrices(self) -> list[EmpresaType]:
        return _armar(empresas.listar_matrices())

    @strawberry.field(description="Una empresa por su id.")
    def empresa(self, id: strawberry.ID) -> EmpresaType | None:
        fila = empresas.obtener_empresa(int(id))
        return _armar([fila])[0] if fila else None

    @strawberry.field(description="Las sucursales DIRECTAS de una empresa.")
    def sucursales(self, empresa_id: strawberry.ID) -> list[EmpresaType]:
        return _armar(empresas.sucursales_de(int(empresa_id)))

    @strawberry.field(
        description="La casa matriz del grupo al que pertenece una empresa. "
        "Si ya es matriz, se devuelve ella misma."
    )
    def matriz_de(self, empresa_id: strawberry.ID) -> EmpresaType | None:
        fila = empresas.matriz_de(int(empresa_id))
        return _armar([fila])[0] if fila else None


@strawberry.type
class EmpresaPaisQueries:
    @strawberry.field(description="Los países donde opera una empresa.")
    def paises_de_empresa(self, empresa_id: strawberry.ID) -> list[EmpresaPaisType]:
        return [
            EmpresaPaisType.desde_modelo(f)
            for f in empresas.listar_paises_de(int(empresa_id))
        ]


@strawberry.type
class EmpresaMonedaQueries:
    @strawberry.field(
        description="Las monedas con las que opera una empresa. La que "
        "tiene esMonedaOficial en true es su base de conversión."
    )
    def monedas_de_empresa(
        self, empresa_id: strawberry.ID
    ) -> list[EmpresaMonedaType]:
        return [
            EmpresaMonedaType.desde_modelo(f)
            for f in empresas.listar_monedas_de(int(empresa_id))
        ]


@strawberry.type
class EmpresaQuery(EmpresaQueries, EmpresaPaisQueries, EmpresaMonedaQueries):
    """La superficie de consulta de empresas. Solo compone."""
