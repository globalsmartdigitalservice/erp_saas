"""Las consultas de entidades."""

import strawberry
from graphql import GraphQLError

from comun.idiomas import api as idiomas
from comun.tipologias import api as tipologias
from comun.tipologias.graphql.types import TipologiaType
from core.graphql import InfoDePagina, Pagina
from core.paginacion import VentanaDemasiadoProfunda
from dominios.entidades import api as entidades
from dominios.entidades.models import CategoriaEntidad
from dominios.seguridad.permisos_graphql import requiere_autenticacion

from .types import (
    CategoriaEntidadType,
    ContactoEntidadType,
    DireccionType,
    EncuestaSatisfaccionType,
    EntidadType,
    RolEntidadType,
)


# El `db_table`, no un literal: es la misma cadena que guarda
# `Traduccion.entidad_tipo` y la que valida el registro de traducibles.
TABLA_CATEGORIA = CategoriaEntidad._meta.db_table


def _categorias_traducidas(filas) -> dict[int, CategoriaEntidadType]:
    """
    Las categorías con su texto en el idioma activo, POR LOTE.

    Copiado de `comun/tipologias/graphql/queries.py`, que es el molde.
    Son DOS consultas fijas —una por campo traducible—, no dos por fila.

    Devuelve un dict porque los dos que lo usan quieren cosas distintas:
    `_armar_roles` busca por id y `categorias_entidad` recorre. El orden
    de inserción es el de `filas`, así que la lista sale ordenada igual
    que antes.

     "Mayorista" la inventó el cliente, así que **solo el cliente
    puede traducirla**. Lo que no tenga traducción sale como fue
    cargado, y eso es lo correcto: media pantalla traducida es lo normal
    en un ERP, no un error.
    """
    filas = list(filas)
    if not filas:
        return {}

    estados = _tipologias_de({f.estado_id for f in filas})
    idioma_id = idiomas.idioma_activo()

    # Sin idioma activo no se consulta nada (panel del proveedor,
    # comandos): cada texto sale como está guardado.
    if idioma_id is None:
        return {
            f.pk: CategoriaEntidadType.desde_modelo(f, estados.get(f.estado_id))
            for f in filas
        }

    ids = [f.pk for f in filas]
    nombres = idiomas.traducciones_de(TABLA_CATEGORIA, ids, "nombre", idioma_id)
    descripciones = idiomas.traducciones_de(
        TABLA_CATEGORIA, ids, "descripcion", idioma_id
    )

    return {
        f.pk: CategoriaEntidadType.desde_modelo(
            f,
            estados.get(f.estado_id),
            nombre=nombres.get(f.pk),
            descripcion=descripciones.get(f.pk),
        )
        for f in filas
    }


def _tipologias_de(*grupos) -> dict[int, TipologiaType]:
    """
    Trae de UNA sola consulta todas las tipologías que se van a necesitar.

    Recibe grupos de ids —normalmente `{f.estado_id for f in filas}`— y
    los junta antes de consultar: si tres campos distintos apuntan a la
    misma fila, se pide una vez.
    """
    ids = set()
    for grupo in grupos:
        ids.update(i for i in grupo if i is not None)

    return {
        id_: TipologiaType.desde_modelo(fila)
        for id_, fila in tipologias.obtener_varias(ids).items()
    }


def _armar_contactos(filas) -> list[ContactoEntidadType]:
    if not filas:
        return []

    estados = _tipologias_de({f.estado_id for f in filas})
    return [
        ContactoEntidadType.desde_modelo(f, estados.get(f.estado_id))
        for f in filas
    ]


def _armar_roles(filas) -> list[RolEntidadType]:
    if not filas:
        return []

    tipos = _tipologias_de(
        {f.tipo_rol_id for f in filas}, {f.estado_id for f in filas}
    )
    # Las categorías, también por lote y también en una sola consulta —
    # más las dos del batch de traducciones, que tampoco crecen por fila.
    categorias = _categorias_traducidas(
        entidades.obtener_categorias(
            {f.categoria_entidad_id for f in filas if f.categoria_entidad_id}
        ).values()
    )

    return [
        RolEntidadType.desde_modelo(
            f,
            tipos.get(f.tipo_rol_id),
            tipos.get(f.estado_id),
            categorias.get(f.categoria_entidad_id),
        )
        for f in filas
    ]


def _armar_direcciones(filas) -> list[DireccionType]:
    if not filas:
        return []

    tipos = _tipologias_de({f.tipo_id for f in filas}, {f.estado_id for f in filas})
    return [
        DireccionType.desde_modelo(f, tipos.get(f.tipo_id), tipos.get(f.estado_id))
        for f in filas
    ]


def _armar_entidades(filas, con_detalle: bool = False) -> list[EntidadType]:
    """
    `con_detalle` llena las cuatro colecciones. Lo usa `entidad(id)`, con
    UNA fila; la lista lo deja en False — ver el aviso de `types.py`.
    """
    if not filas:
        return []

    tipos = _tipologias_de(
        {f.tipo_entidad_id for f in filas},
        {f.tipo_documento_id for f in filas},
        {f.regimen_tributario_id for f in filas},
        {f.estado_id for f in filas},
    )

    armadas = []
    for f in filas:
        detalle = {}
        if con_detalle:
            detalle = {
                "roles": _armar_roles(entidades.listar_roles_de(f.pk)),
                "direcciones": _armar_direcciones(
                    entidades.listar_direcciones_de(f.pk)
                ),
                "contactos": _armar_contactos(
                    entidades.listar_contactos_de(f.pk)
                ),
                "encuestas": [
                    EncuestaSatisfaccionType.desde_modelo(e)
                    for e in entidades.listar_encuestas_de(f.pk)
                ],
            }

        armadas.append(
            EntidadType.desde_modelo(
                f,
                tipos.get(f.tipo_entidad_id),
                tipos.get(f.tipo_documento_id),
                tipos.get(f.regimen_tributario_id),
                tipos.get(f.estado_id),
                **detalle,
            )
        )

    return armadas


@strawberry.type
class EntidadQueries:
    @strawberry.field(
        description="Las entidades de la empresa activa, DE A PÁGINAS. Por "
        "defecto 25, tope 100. SIN sus colecciones: para roles, direcciones, "
        "contactos y encuestas usá `entidad(id)` o las consultas sueltas."
    )
    @requiere_autenticacion
    def entidades(
        self,
        info: strawberry.Info,
        limite: int | None = None,
        desde: int = 0,
    ) -> Pagina[EntidadType]:
        try:
            pagina = entidades.listar_entidades(limite=limite, desde=desde)
        except VentanaDemasiadoProfunda as error:
            # No es un bug ni un dato inválido: es el sistema diciendo
            # "filtrá". El mensaje ya explica qué hacer.
            raise GraphQLError(str(error)) from error

        return Pagina(
            items=_armar_entidades(pagina.items),
            info=InfoDePagina.desde_pagina(pagina),
        )

    @strawberry.field(
        description="Una entidad con TODO: sus roles, direcciones, contactos "
        "y encuestas."
    )
    @requiere_autenticacion
    def entidad(self, info: strawberry.Info, id: strawberry.ID) -> EntidadType | None:
        fila = entidades.obtener_entidad(int(id))
        if fila is None:
            return None
        return _armar_entidades([fila], con_detalle=True)[0]

    @strawberry.field(
        description="Busca una entidad por su documento. El documento vacío "
        "no se busca: todas las que no lo tienen empatarían."
    )
    @requiere_autenticacion
    def entidad_por_documento(
        self, info: strawberry.Info, documento: str
    ) -> EntidadType | None:
        fila = entidades.buscar_entidad_por_documento(documento)
        if fila is None:
            return None
        return _armar_entidades([fila])[0]


@strawberry.type
class CategoriaEntidadQueries:
    @strawberry.field(
        description="Las categorías de entidad de la empresa activa. El "
        "nombre y la descripción vienen en el idioma activo; lo que no esté "
        "traducido sale como lo cargó el cliente."
    )
    @requiere_autenticacion
    def categorias_entidad(self, info: strawberry.Info) -> list[CategoriaEntidadType]:
        return list(
            _categorias_traducidas(entidades.listar_categorias()).values()
        )


@strawberry.type
class DetalleDeEntidadQueries:
    """
    Las colecciones sueltas. Existen para que el frontend pueda pedir solo
    una sin arrastrar el resto del detalle.
    """

    @strawberry.field(description="Los roles de una entidad.")
    @requiere_autenticacion
    def roles_de_entidad(
        self, info: strawberry.Info, entidad_id: strawberry.ID
    ) -> list[RolEntidadType]:
        return _armar_roles(entidades.listar_roles_de(int(entidad_id)))

    @strawberry.field(description="Las direcciones de una entidad.")
    @requiere_autenticacion
    def direcciones_de_entidad(
        self,
        info: strawberry.Info,
        entidad_id: strawberry.ID,
    ) -> list[DireccionType]:
        return _armar_direcciones(entidades.listar_direcciones_de(int(entidad_id)))

    @strawberry.field(description="Los contactos de una entidad.")
    @requiere_autenticacion
    def contactos_de_entidad(
        self,
        info: strawberry.Info,
        entidad_id: strawberry.ID,
    ) -> list[ContactoEntidadType]:
        return _armar_contactos(entidades.listar_contactos_de(int(entidad_id)))

    @strawberry.field(description="Las encuestas de una entidad, de la más nueva.")
    @requiere_autenticacion
    def encuestas_de_entidad(
        self,
        info: strawberry.Info,
        entidad_id: strawberry.ID,
    ) -> list[EncuestaSatisfaccionType]:
        return [
            EncuestaSatisfaccionType.desde_modelo(e)
            for e in entidades.listar_encuestas_de(int(entidad_id))
        ]


@strawberry.type
class EntidadesQuery(
    EntidadQueries, CategoriaEntidadQueries, DetalleDeEntidadQueries
):
    """La superficie de consulta de entidades. Solo compone."""
