"""Las mutations de entidades."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import (
    requiere_autenticacion,
    requiere_permiso,
)

from dominios.entidades import api as entidades

from .inputs import (
    ActualizarCategoriaEntidadInput,
    ActualizarContactoEntidadInput,
    ActualizarDireccionInput,
    ActualizarEntidadInput,
    ActualizarRolEntidadInput,
    CrearCategoriaEntidadInput,
    CrearContactoEntidadInput,
    CrearDireccionInput,
    CrearEntidadInput,
    CrearRolEntidadInput,
    RegistrarEncuestaInput,
)
from .queries import (
    _armar_contactos,
    _armar_direcciones,
    _armar_entidades,
    _armar_roles,
    _categorias_traducidas,
)
from .types import (
    CategoriaEntidadType,
    ContactoEntidadType,
    DireccionType,
    EncuestaSatisfaccionType,
    EntidadType,
    RolEntidadType,
)


def _armar_categoria(fila) -> CategoriaEntidadType:
    """Por el mismo camino que la lista: con su estado y su traducción."""
    return _categorias_traducidas([fila])[fila.pk]


def _traducir(error: ValidationError) -> GraphQLError:
    """
    Un `ValidationError` del dominio es un error ESPERADO: el mensaje va
    tal cual al cliente. Cualquier otra excepción sube sin tocar, para
    que no se disfrace un bug de error de validación.
    """
    return GraphQLError("; ".join(error.messages))


def _id(valor) -> int | None:
    return None if valor is None else int(valor)


def _campos(datos, *nombres) -> dict:
    """
    Los campos que llegaron con valor. Los que terminan en `_id` se
    pasan a entero, porque en GraphQL viajan como `ID` (string).
    """
    salida = {}
    for nombre in nombres:
        valor = getattr(datos, nombre)
        if valor is None:
            continue
        salida[nombre] = _id(valor) if nombre.endswith("_id") else valor
    return salida


@auto_permisos(recurso="ENT_ENTIDADES")
@strawberry.type
class EntidadMutations:
    @strawberry.mutation(description="Crea una entidad en la empresa activa.")
    @requiere_autenticacion
    @requiere_permiso("ent_entidades_crear_entidad")
    def crear_entidad(
        self, info: strawberry.Info, datos: CrearEntidadInput
    ) -> EntidadType:
        try:
            fila = entidades.crear_entidad(
                tipo_entidad_id=int(datos.tipo_entidad_id),
                nombre=datos.nombre,
                tipo_documento_id=int(datos.tipo_documento_id),
                estado_id=int(datos.estado_id),
                pri_apellido=datos.pri_apellido,
                seg_apellido=datos.seg_apellido,
                documento=datos.documento,
                regimen_tributario_id=_id(datos.regimen_tributario_id),
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_entidades([fila])[0]

    @strawberry.mutation(description="Actualiza una entidad. Solo lo que mandes.")
    @requiere_autenticacion
    @requiere_permiso("ent_entidades_actualizar_entidad")
    def actualizar_entidad(
        self, info: strawberry.Info, id: strawberry.ID, datos: ActualizarEntidadInput
    ) -> EntidadType:
        try:
            fila = entidades.actualizar_entidad(
                int(id),
                **_campos(
                    datos,
                    "tipo_entidad_id",
                    "nombre",
                    "pri_apellido",
                    "seg_apellido",
                    "tipo_documento_id",
                    "documento",
                    "regimen_tributario_id",
                    "estado_id",
                ),
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_entidades([fila])[0]

    @strawberry.mutation(
        description="Da de baja una entidad. Soft delete: no se borra, y "
        "sus roles y direcciones quedan intactos."
    )
    @requiere_autenticacion
    @requiere_permiso("ent_entidades_desactivar_entidad")
    def desactivar_entidad(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> EntidadType:
        try:
            fila = entidades.desactivar_entidad(int(id))
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_entidades([fila])[0]


@auto_permisos(recurso="ENT_CATEGORIAS")
@strawberry.type
class CategoriaEntidadMutations:
    @strawberry.mutation(description="Crea una categoría de entidad.")
    @requiere_autenticacion
    @requiere_permiso("ent_categorias_crear_categoria_entidad")
    def crear_categoria_entidad(
        self, info: strawberry.Info, datos: CrearCategoriaEntidadInput
    ) -> CategoriaEntidadType:
        try:
            fila = entidades.crear_categoria(
                nombre=datos.nombre,
                descripcion=datos.descripcion,
                descuento_categ_cliente=datos.descuento_categ_cliente,
                lista_precio_id=datos.lista_precio_id,
                estado_id=int(datos.estado_id),
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_categoria(fila)

    @strawberry.mutation(description="Actualiza una categoría de entidad.")
    @requiere_autenticacion
    @requiere_permiso("ent_categorias_actualizar_categoria_entidad")
    def actualizar_categoria_entidad(
        self,
        info: strawberry.Info,
        id: strawberry.ID,
        datos: ActualizarCategoriaEntidadInput,
    ) -> CategoriaEntidadType:
        try:
            fila = entidades.actualizar_categoria(
                int(id),
                **_campos(
                    datos,
                    "nombre",
                    "descripcion",
                    "descuento_categ_cliente",
                    "lista_precio_id",
                    "estado_id",
                ),
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_categoria(fila)

    @strawberry.mutation(
        description="Da de baja una categoría. Soft delete: los roles que "
        "ya la tienen asignada no se tocan."
    )
    @requiere_autenticacion
    @requiere_permiso("ent_categorias_desactivar_categoria_entidad")
    def desactivar_categoria_entidad(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> CategoriaEntidadType:
        try:
            fila = entidades.desactivar_categoria(int(id))
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_categoria(fila)


@auto_permisos(recurso="ENT_ROLES")
@strawberry.type
class RolEntidadMutations:
    @strawberry.mutation(
        description="Le da un rol a una entidad: cliente, proveedor, etc."
    )
    @requiere_autenticacion
    @requiere_permiso("ent_roles_crear_rol_entidad")
    def crear_rol_entidad(
        self, info: strawberry.Info, datos: CrearRolEntidadInput
    ) -> RolEntidadType:
        try:
            fila = entidades.crear_rol(
                entidad_id=int(datos.entidad_id),
                tipo_rol_id=int(datos.tipo_rol_id),
                estado_id=int(datos.estado_id),
                categoria_entidad_id=_id(datos.categoria_entidad_id),
                limite_credito=datos.limite_credito,
                datos_rol=datos.datos_rol,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_roles([fila])[0]

    @strawberry.mutation(
        description="Actualiza un rol. La entidad y el tipo NO se cambian: "
        "son lo que ese rol es."
    )
    @requiere_autenticacion
    @requiere_permiso("ent_roles_actualizar_rol_entidad")
    def actualizar_rol_entidad(
        self, info: strawberry.Info, id: strawberry.ID, datos: ActualizarRolEntidadInput
    ) -> RolEntidadType:
        try:
            fila = entidades.actualizar_rol(
                int(id),
                **_campos(
                    datos,
                    "categoria_entidad_id",
                    "limite_credito",
                    "datos_rol",
                    "estado_id",
                ),
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_roles([fila])[0]

    @strawberry.mutation(
        description="Da de baja un rol. La entidad sigue existiendo; deja "
        "de actuar en ese papel."
    )
    @requiere_autenticacion
    @requiere_permiso("ent_roles_desactivar_rol_entidad")
    def desactivar_rol_entidad(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> RolEntidadType:
        try:
            fila = entidades.desactivar_rol(int(id))
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_roles([fila])[0]


@auto_permisos(recurso="ENT_DETALLES")
@strawberry.type
class DetalleDeEntidadMutations:
    @strawberry.mutation(description="Le agrega una dirección a una entidad.")
    @requiere_autenticacion
    @requiere_permiso("ent_detalles_crear_direccion")
    def crear_direccion(
        self, info: strawberry.Info, datos: CrearDireccionInput
    ) -> DireccionType:
        try:
            fila = entidades.crear_direccion(
                entidad_id=int(datos.entidad_id),
                tipo_id=int(datos.tipo_id),
                estado_id=int(datos.estado_id),
                calle=datos.calle,
                numero=datos.numero,
                descripcion=datos.descripcion,
                ubicacion_geografica_id=_id(datos.ubicacion_geografica_id),
                direccion_texto=datos.direccion_texto,
                latitud=datos.latitud,
                longitud=datos.longitud,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_direcciones([fila])[0]

    @strawberry.mutation(description="Actualiza una dirección.")
    @requiere_autenticacion
    @requiere_permiso("ent_detalles_actualizar_direccion")
    def actualizar_direccion(
        self, info: strawberry.Info, id: strawberry.ID, datos: ActualizarDireccionInput
    ) -> DireccionType:
        try:
            fila = entidades.actualizar_direccion(
                int(id),
                **_campos(
                    datos,
                    "tipo_id",
                    "calle",
                    "numero",
                    "descripcion",
                    "ubicacion_geografica_id",
                    "direccion_texto",
                    "latitud",
                    "longitud",
                    "estado_id",
                ),
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_direcciones([fila])[0]

    @strawberry.mutation(description="Da de baja una dirección. Soft delete.")
    @requiere_autenticacion
    @requiere_permiso("ent_detalles_desactivar_direccion")
    def desactivar_direccion(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> DireccionType:
        try:
            fila = entidades.desactivar_direccion(int(id))
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_direcciones([fila])[0]

    @strawberry.mutation(description="Le agrega un contacto a una entidad.")
    @requiere_autenticacion
    @requiere_permiso("ent_detalles_crear_contacto_entidad")
    def crear_contacto_entidad(
        self, info: strawberry.Info, datos: CrearContactoEntidadInput
    ) -> ContactoEntidadType:
        try:
            fila = entidades.crear_contacto(
                entidad_id=int(datos.entidad_id),
                nombre=datos.nombre,
                cargo=datos.cargo,
                email=datos.email,
                telefono=datos.telefono,
                estado_id=int(datos.estado_id),
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_contactos([fila])[0]

    @strawberry.mutation(description="Actualiza un contacto.")
    @requiere_autenticacion
    @requiere_permiso("ent_detalles_actualizar_contacto_entidad")
    def actualizar_contacto_entidad(
        self,
        info: strawberry.Info,
        id: strawberry.ID,
        datos: ActualizarContactoEntidadInput,
    ) -> ContactoEntidadType:
        try:
            fila = entidades.actualizar_contacto(
                int(id),
                **_campos(
                    datos, "nombre", "cargo", "email", "telefono", "estado_id"
                ),
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_contactos([fila])[0]

    @strawberry.mutation(description="Da de baja un contacto. Soft delete.")
    @requiere_autenticacion
    @requiere_permiso("ent_detalles_desactivar_contacto_entidad")
    def desactivar_contacto_entidad(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> ContactoEntidadType:
        try:
            fila = entidades.desactivar_contacto(int(id))
        except ValidationError as error:
            raise _traducir(error) from error

        return _armar_contactos([fila])[0]

    @strawberry.mutation(
        description="Registra una encuesta de satisfacción. No se edita ni "
        "se da de baja: es un hecho ocurrido en una fecha."
    )
    @requiere_autenticacion
    @requiere_permiso("ent_detalles_registrar_encuesta")
    def registrar_encuesta(
        self, info: strawberry.Info, datos: RegistrarEncuestaInput
    ) -> EncuestaSatisfaccionType:
        try:
            fila = entidades.registrar_encuesta(
                entidad_id=int(datos.entidad_id),
                fecha=datos.fecha,
                puntaje=datos.puntaje,
                comentario=datos.comentario,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return EncuestaSatisfaccionType.desde_modelo(fila)


@strawberry.type
class EntidadesMutation(
    EntidadMutations,
    CategoriaEntidadMutations,
    RolEntidadMutations,
    DetalleDeEntidadMutations,
):
    """La superficie de escritura de entidades. Solo compone."""
