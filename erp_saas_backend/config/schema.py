"""
El schema raíz de GraphQL. La única puerta de entrada de la API.

Cada app hoja escribe su propia `XxxQuery` y `XxxMutation` en su carpeta
`graphql/`. Acá **solo se componen**: no se escribe
ni un resolver.

Agregar una app es agregar un nombre a las listas de herencia — el
schema se extiende sin modificarse.

OJO CON LOS NOMBRES
    Todas las apps terminan fusionadas en una sola `Query`, así que los
    nombres de los campos son GLOBALES en todo el sistema. Con ~40 apps,
    dos que definan `listar` chocan. Por eso la convención es sustantivo
    específico: `paises`, `monedas`, nunca genéricos.
"""

import strawberry

from core.graphql import EnmascararErrores, SchemaDelErp

from comun.catalogo_modulos.graphql.queries import CatalogoModulosQuery
from comun.empresas.graphql.mutations import EmpresaMutation
from comun.empresas.graphql.queries import EmpresaQuery
from comun.membresias.graphql.mutations import MembresiaMutation
from comun.membresias.graphql.queries import MembresiaQuery
from comun.geografia.graphql.mutations import GeografiaMutation
from comun.geografia.graphql.queries import GeografiaQuery
from comun.idiomas.graphql.mutations import IdiomaMutation
from comun.idiomas.graphql.queries import IdiomaQuery
from comun.monedas.graphql.mutations import MonedaMutation
from comun.monedas.graphql.queries import MonedaQuery
from comun.tipologias.graphql.mutations import TipologiaMutation
from comun.tipologias.graphql.queries import TipologiaQuery
from comun.usuarios.graphql.mutations import UsuarioMutation
from comun.usuarios.graphql.queries import UsuarioQuery
from dominios.entidades.graphql.mutations import EntidadesMutation
from dominios.entidades.graphql.queries import EntidadesQuery
from dominios.seguridad.graphql.login import LoginMutation
from dominios.seguridad.graphql.mutations import SeguridadMutation
from dominios.seguridad.graphql.queries import SeguridadQuery
from dominios.seguridad.password_pendiente import ExigirCambioDePassword
from procesos.graphql.mutations import ProcesosMutation


@strawberry.type
class Query(
    GeografiaQuery,
    TipologiaQuery,
    MonedaQuery,
    IdiomaQuery,
    EmpresaQuery,
    EntidadesQuery,
    # ── Módulo 12 — Usuarios y Seguridad ──
    UsuarioQuery,
    MembresiaQuery,
    CatalogoModulosQuery,
    SeguridadQuery,
):
    @strawberry.field(description="Comprobación de que el endpoint responde.")
    def version(self) -> str:
        return "erp-backend 0.1.0"


@strawberry.type
class Mutation(
    GeografiaMutation,
    TipologiaMutation,
    MonedaMutation,
    IdiomaMutation,
    EmpresaMutation,
    EntidadesMutation,
    # ── Módulo 12 — Usuarios y Seguridad ──
    UsuarioMutation,
    MembresiaMutation,
    SeguridadMutation,
    LoginMutation,
    ProcesosMutation,
):
    pass



schema = SchemaDelErp(
    query=Query,
    mutation=Mutation,
    extensions=[EnmascararErrores(), ExigirCambioDePassword()],
)
