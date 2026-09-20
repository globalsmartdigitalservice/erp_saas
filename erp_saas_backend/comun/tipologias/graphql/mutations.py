"""Las mutations de tipologías."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import (
    requiere_autenticacion,
    requiere_permiso,
)

from comun.tipologias import api as tipologias

from .inputs import ActualizarTipologiaInput, CrearTipologiaInput
from .types import TipologiaType


def _traducir(error: ValidationError) -> GraphQLError:
    return GraphQLError("; ".join(error.messages))


@auto_permisos(recurso="CONF_TIPOLOGIAS")
@strawberry.type
class TipologiaMutations:
    @strawberry.mutation(
        description="Agrega un valor propio a una lista. La empresa sale del "
        "contexto, no del input."
    )
    @requiere_autenticacion
    @requiere_permiso("conf_tipologias_crear_tipologia")
    def crear_tipologia(
        self, info: strawberry.Info, datos: CrearTipologiaInput
    ) -> TipologiaType:
        try:
            fila = tipologias.crear(
                agrupador=datos.agrupador,
                nombre=datos.nombre,
                abreviatura=datos.abreviatura,
                indice=datos.indice,
            )
        except ValidationError as e:
            raise _traducir(e) from e
        return TipologiaType.desde_modelo(fila)

    @strawberry.mutation(
        description="Modifica una tipología propia. Rechaza las del sistema."
    )
    @requiere_autenticacion
    @requiere_permiso("conf_tipologias_actualizar_tipologia")
    def actualizar_tipologia(
        self, info: strawberry.Info, id: strawberry.ID, datos: ActualizarTipologiaInput
    ) -> TipologiaType:
        campos = {
            "nombre": datos.nombre,
            "abreviatura": datos.abreviatura,
            "indice": datos.indice,
        }
        try:
            fila = tipologias.actualizar(
                int(id), **{k: v for k, v in campos.items() if v is not None}
            )
        except ValidationError as e:
            raise _traducir(e) from e
        return TipologiaType.desde_modelo(fila)

    @strawberry.mutation(
        description="Da de baja una tipología PROPIA. Soft delete: pasa a "
        "estado Inactivo, la fila no se borra. Afecta a todo el grupo: si la "
        "empresa tiene sucursales, ellas también dejan de verla. Rechaza las "
        "de fábrica y las heredadas de la matriz — para ésas va ocultar."
    )
    @requiere_autenticacion
    @requiere_permiso("conf_tipologias_desactivar_tipologia")
    def desactivar_tipologia(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> TipologiaType:
        try:
            fila = tipologias.desactivar(int(id))
        except ValidationError as e:
            raise _traducir(e) from e
        return TipologiaType.desde_modelo(fila)

    @strawberry.mutation(
        description="La empresa activa deja de ver ese valor. SOLO ella: la "
        "matriz y las demás sucursales lo siguen viendo. Sirve para lo "
        "heredado y para lo propio. Idempotente."
    )
    @requiere_autenticacion
    @requiere_permiso("conf_tipologias_ocultar_tipologia")
    def ocultar_tipologia(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        try:
            tipologias.ocultar(int(id))
        except ValidationError as e:
            raise _traducir(e) from e
        return True

    @strawberry.mutation(
        description="Vuelve a mostrar un valor oculto. Devuelve False si no "
        "estaba oculto — no es un error, ya se veía."
    )
    @requiere_autenticacion
    @requiere_permiso("conf_tipologias_mostrar_tipologia")
    def mostrar_tipologia(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        try:
            borradas = tipologias.mostrar(int(id))
        except ValidationError as e:
            raise _traducir(e) from e
        return borradas > 0


@strawberry.type
class TipologiaMutation(TipologiaMutations):
    """La superficie de escritura de tipologías. Solo compone."""
