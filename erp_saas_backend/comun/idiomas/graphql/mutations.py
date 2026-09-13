"""Las mutations de idiomas."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import solo_proveedor

from comun.idiomas import api as idiomas

from core.tenancy import empresa_actual

from .inputs import ActualizarIdiomaInput, CrearIdiomaInput, GuardarTraduccionInput
from .types import IdiomaType, TraduccionType


def _traducir(error: ValidationError) -> GraphQLError:
    """
    Un `ValidationError` del dominio es un error ESPERADO: el mensaje va
    tal cual al cliente. Cualquier otra excepción sube sin tocar, para
    que no se disfrace un bug de error de validación.
    """
    return GraphQLError("; ".join(error.messages))


@auto_permisos(recurso="IDIO_IDIOMAS")
@strawberry.type
class IdiomaMutations:
    @strawberry.mutation(description="Crea un idioma. Catálogo del sistema.")
    @solo_proveedor
    def crear_idioma(self, info: strawberry.Info, datos: CrearIdiomaInput) -> IdiomaType:
        try:
            fila = idiomas.crear_idioma(
                codigo=datos.codigo, nombre=datos.nombre, activo=datos.activo
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return IdiomaType.desde_modelo(fila)

    @strawberry.mutation(
        description="Cambia el código o el nombre. Para prenderlo o apagarlo "
        "están activarIdioma y desactivarIdioma."
    )
    @solo_proveedor
    def actualizar_idioma(
        self,
        info: strawberry.Info,
        id: strawberry.ID, datos: ActualizarIdiomaInput
    ) -> IdiomaType:
        campos = {
            campo: valor
            for campo, valor in (("codigo", datos.codigo), ("nombre", datos.nombre))
            if valor is not None
        }
        try:
            fila = idiomas.actualizar_idioma(int(id), **campos)
        except ValidationError as error:
            raise _traducir(error) from error
        return IdiomaType.desde_modelo(fila)

    @strawberry.mutation(
        description="Soft delete: la fila queda, deja de ofrecerse. Es "
        "idempotente."
    )
    @solo_proveedor
    def desactivar_idioma(self, info: strawberry.Info, id: strawberry.ID) -> IdiomaType:
        try:
            fila = idiomas.desactivar_idioma(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return IdiomaType.desde_modelo(fila)

    @strawberry.mutation(description="Vuelve a habilitar un idioma. Es idempotente.")
    @solo_proveedor
    def activar_idioma(self, info: strawberry.Info, id: strawberry.ID) -> IdiomaType:
        try:
            fila = idiomas.activar_idioma(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return IdiomaType.desde_modelo(fila)


@auto_permisos(recurso="IDIO_TRADUCCIONES")
@strawberry.type
class TraduccionMutations:
    """
     ACÁ NO ESTÁ `guardar_traduccion_de_fabrica`, y es a propósito.

    Esa escribe el catálogo del sistema, que ven TODOS los clientes.
    Corre solo dentro de `sin_filtro_de_empresa()` —semillas y panel del
    proveedor—, así que no se expone en el endpoint que usa el cliente.
    """

    @strawberry.mutation(
        description="Guarda la traducción de un campo. Si la empresa ya "
        "tenía una para ese campo y ese idioma, la reemplaza; si no, la "
        "crea. Nunca pisa la de fábrica ni la de la casa matriz: la propia "
        "les gana al leer."
    )
    @solo_proveedor
    def guardar_traduccion(self, info: strawberry.Info, datos: GuardarTraduccionInput) -> TraduccionType:
        try:
            fila = idiomas.guardar_traduccion(
                entidad_tipo=datos.entidad_tipo,
                entidad_id=datos.entidad_id,
                campo=datos.campo,
                idioma_id=int(datos.idioma_id),
                texto=datos.texto,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        idioma = idiomas.obtener_idioma(fila.idioma_id)
        return TraduccionType.desde_modelo(
            fila,
            IdiomaType.desde_modelo(idioma),
            es_propia=fila.empresa_id is not None
            and fila.empresa_id == empresa_actual(),
        )

    @strawberry.mutation(
        description="Saca una traducción: el registro vuelve a mostrarse "
        "en su idioma original. Solo se borran las propias."
    )
    @solo_proveedor
    def borrar_traduccion(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        try:
            idiomas.borrar_traduccion(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return True


@strawberry.type
class IdiomaMutation(IdiomaMutations, TraduccionMutations):
    """La superficie de escritura de idiomas. Solo compone."""
