"""Las mutations de geografía."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos

from comun.geografia import api as geografia
from comun.tipologias import api as tipologias
from comun.tipologias.graphql.types import TipologiaType

from .inputs import ActualizarPaisInput, CrearPaisInput, CrearUbicacionInput
from .types import PaisType, UbicacionGeograficaType


def _estado_de(fila) -> TipologiaType | None:
    tipologia = tipologias.obtener_varias([fila.estado_id]).get(fila.estado_id)
    return TipologiaType.desde_modelo(tipologia) if tipologia else None


def _a_pais(fila) -> PaisType:
    return PaisType.desde_modelo(fila, _estado_de(fila))


def _a_ubicacion(fila) -> UbicacionGeograficaType:
    return UbicacionGeograficaType.desde_modelo(fila, _estado_de(fila))


def _traducir(error: ValidationError) -> GraphQLError:
    """
    Un `ValidationError` del dominio es un error ESPERADO: el mensaje va
    tal cual al cliente. Cualquier otra excepción sube sin tocar, para
    que no se disfrace un bug de error de validación.
    """
    return GraphQLError("; ".join(error.messages))


@auto_permisos(recurso="CORE_PAISES")
@strawberry.type
class PaisMutations:
    @strawberry.mutation(description="Crea un país. Catálogo del sistema.")
    def crear_pais(self, datos: CrearPaisInput) -> PaisType:
        try:
            fila = geografia.crear_pais(
                cod_pais=datos.cod_pais,
                nombre=datos.nombre,
                codigo_iso=datos.codigo_iso,
                estado_id=int(datos.estado_id),
            )
        except ValidationError as e:
            raise _traducir(e) from e
        return _a_pais(fila)

    @strawberry.mutation(description="Actualiza los campos enviados de un país.")
    def actualizar_pais(self, id: strawberry.ID, datos: ActualizarPaisInput) -> PaisType:
        campos = {
            "cod_pais": datos.cod_pais,
            "nombre": datos.nombre,
            "codigo_iso": datos.codigo_iso,
            "estado_id": int(datos.estado_id) if datos.estado_id else None,
        }
        try:
            fila = geografia.actualizar_pais(
                int(id), **{k: v for k, v in campos.items() if v is not None}
            )
        except ValidationError as e:
            raise _traducir(e) from e
        return _a_pais(fila)

    @strawberry.mutation(
        description="Da de baja un país. Soft delete: pasa al estado Baja, "
        "no se borra."
    )
    def desactivar_pais(self, id: strawberry.ID) -> PaisType:
        try:
            fila = geografia.desactivar_pais(int(id))
        except ValidationError as e:
            raise _traducir(e) from e
        return _a_pais(fila)


@auto_permisos(recurso="CORE_UBICACIONES")
@strawberry.type
class UbicacionMutations:
    @strawberry.mutation(
        description="Crea una división geográfica. El nivel lo calcula el "
        "sistema a partir del padre."
    )
    def crear_ubicacion(self, datos: CrearUbicacionInput) -> UbicacionGeograficaType:
        try:
            fila = geografia.crear_ubicacion(
                pais_id=int(datos.pais_id),
                nombre=datos.nombre,
                tipo=datos.tipo,
                estado_id=int(datos.estado_id),
                division_superior_id=(
                    int(datos.division_superior_id)
                    if datos.division_superior_id
                    else None
                ),
                codigo=datos.codigo,
            )
        except ValidationError as e:
            raise _traducir(e) from e
        return _a_ubicacion(fila)

    @strawberry.mutation(
        description="Cambia de quién cuelga una ubicación. Rechaza el "
        "movimiento si formaría un ciclo."
    )
    def mover_ubicacion(
        self, id: strawberry.ID, nuevo_padre_id: strawberry.ID | None = None
    ) -> UbicacionGeograficaType:
        try:
            fila = geografia.mover_ubicacion(
                int(id), int(nuevo_padre_id) if nuevo_padre_id else None
            )
        except ValidationError as e:
            raise _traducir(e) from e
        return _a_ubicacion(fila)

    @strawberry.mutation(description="Da de baja una ubicación. Soft delete.")
    def desactivar_ubicacion(self, id: strawberry.ID) -> UbicacionGeograficaType:
        try:
            fila = geografia.desactivar_ubicacion(int(id))
        except ValidationError as e:
            raise _traducir(e) from e
        return _a_ubicacion(fila)


@strawberry.type
class GeografiaMutation(PaisMutations, UbicacionMutations):
    """La superficie de escritura de geografía. Solo compone."""
