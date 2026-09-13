"""Las consultas de empresas."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from comun.empresas import api as empresas
from comun.tipologias import api as tipologias
from comun.tipologias.graphql.types import TipologiaType
from dominios.seguridad.permisos_graphql import (
    requiere_autenticacion,
    solo_proveedor,
)

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


def _del_grupo(empresa_id: strawberry.ID) -> int:
    """El id que llegó de afuera, comprobado contra el grupo de la sesión.

    `Empresa` no lleva el filtro de tenancy, así que un id recibido por
    parámetro es exactamente lo que hay que desconfiar: sin esto,
    `sucursales(empresaId: 99)` devuelve las de otro cliente.
    """
    try:
        return empresas.exigir_del_grupo(int(empresa_id))
    except ValidationError as error:
        raise GraphQLError("; ".join(error.messages)) from error


@strawberry.type
class EmpresaQueries:
    @strawberry.field(description="Todas las empresas del sistema.")
    @solo_proveedor
    def empresas(self, info: strawberry.Info) -> list[EmpresaType]:
        return _armar(empresas.listar_empresas())

    @strawberry.field(
        description="Las casas matriz: las que no dependen de ninguna otra. "
        "Un cliente del SaaS = una matriz."
    )
    @solo_proveedor
    def matrices(self, info: strawberry.Info) -> list[EmpresaType]:
        return _armar(empresas.listar_matrices())

    @strawberry.field(description="Una empresa por su id.")
    @requiere_autenticacion
    def empresa(self, info: strawberry.Info, id: strawberry.ID) -> EmpresaType | None:
        fila = empresas.obtener_empresa(_del_grupo(id))
        return _armar([fila])[0] if fila else None

    @strawberry.field(description="Las sucursales DIRECTAS de una empresa.")
    @requiere_autenticacion
    def sucursales(
        self, info: strawberry.Info, empresa_id: strawberry.ID
    ) -> list[EmpresaType]:
        return _armar(empresas.sucursales_de(_del_grupo(empresa_id)))

    @strawberry.field(
        description="La casa matriz del grupo al que pertenece una empresa. "
        "Si ya es matriz, se devuelve ella misma."
    )
    @requiere_autenticacion
    def matriz_de(
        self, info: strawberry.Info, empresa_id: strawberry.ID
    ) -> EmpresaType | None:
        fila = empresas.matriz_de(_del_grupo(empresa_id))
        return _armar([fila])[0] if fila else None


@strawberry.type
class EmpresaPaisQueries:
    @strawberry.field(description="Los países donde opera una empresa.")
    @requiere_autenticacion
    def paises_de_empresa(
        self, info: strawberry.Info, empresa_id: strawberry.ID
    ) -> list[EmpresaPaisType]:
        return [
            EmpresaPaisType.desde_modelo(f)
            for f in empresas.listar_paises_de(_del_grupo(empresa_id))
        ]


@strawberry.type
class EmpresaMonedaQueries:
    @strawberry.field(
        description="Las monedas con las que opera una empresa. La que "
        "tiene esMonedaOficial en true es su base de conversión."
    )
    @requiere_autenticacion
    def monedas_de_empresa(
        self, info: strawberry.Info, empresa_id: strawberry.ID
    ) -> list[EmpresaMonedaType]:
        return [
            EmpresaMonedaType.desde_modelo(f)
            for f in empresas.listar_monedas_de(_del_grupo(empresa_id))
        ]


@strawberry.type
class EmpresaQuery(EmpresaQueries, EmpresaPaisQueries, EmpresaMonedaQueries):
    """La superficie de consulta de empresas. Solo compone."""
