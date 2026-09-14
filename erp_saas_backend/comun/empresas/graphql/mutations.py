"""Las mutations de empresas."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from core.tenancy import empresa_actual
from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import (
    requiere_autenticacion,
    requiere_permiso,
    solo_proveedor,
)

from comun.empresas import api as empresas

from .inputs import (
    ActualizarEmpresaInput,
    ActualizarPaisDeEmpresaInput,
    AgregarPaisInput,
    CrearEmpresaInput,
)
from .queries import _armar
from .types import EmpresaMonedaType, EmpresaPaisType, EmpresaType


def _traducir(error: ValidationError) -> GraphQLError:
    """El mensaje del dominio va tal cual; cualquier otra excepción sube."""
    return GraphQLError("; ".join(error.messages))


def _a_empresa(fila) -> EmpresaType:
    return _armar([fila])[0]


def _id(valor) -> int | None:
    return int(valor) if valor is not None else None


def _empresa_de_la_sesion() -> int:
    """La empresa donde está parado quien llama.

    No se recibe por parámetro: si viniera de afuera, cualquiera escribiría
    dentro de otro cliente mandando un número."""
    empresa_id = empresa_actual()
    if empresa_id is None:
        raise GraphQLError("No hay una empresa activa en la sesión.")
    return empresa_id


@auto_permisos(recurso="CORE_EMPRESAS")
@strawberry.type
class EmpresaMutations:
    @strawberry.mutation(
        description="Alta de un cliente. Crea la empresa y su primer país en "
        "una sola transacción."
    )
    @solo_proveedor
    def crear_empresa(self, info: strawberry.Info, datos: CrearEmpresaInput) -> EmpresaType:
        try:
            fila = empresas.crear_empresa(
                ident_tributaria=datos.ident_tributaria,
                razon_social=datos.razon_social,
                nombre_comercial=datos.nombre_comercial,
                tipo_empresa_id=int(datos.tipo_empresa_id),
                rubro_id=int(datos.rubro_id),
                estado_id=int(datos.estado_id),
                idioma_default_id=int(datos.idioma_default_id),
                moneda_oficial_id=int(datos.moneda_oficial_id),
                pais_id=int(datos.pais_id),
                empresa_padre_id=_id(datos.empresa_padre_id),
                ubicacion_geografica_id=_id(datos.ubicacion_geografica_id),
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_empresa(fila)

    @strawberry.mutation(description="Cambia los datos de una empresa.")
    @solo_proveedor
    def actualizar_empresa(
        self,
        info: strawberry.Info,
        id: strawberry.ID, datos: ActualizarEmpresaInput
    ) -> EmpresaType:
        campos = {
            campo: valor
            for campo, valor in (
                ("ident_tributaria", datos.ident_tributaria),
                ("razon_social", datos.razon_social),
                ("nombre_comercial", datos.nombre_comercial),
                ("tipo_empresa_id", _id(datos.tipo_empresa_id)),
                ("rubro_id", _id(datos.rubro_id)),
                ("estado_id", _id(datos.estado_id)),
                ("idioma_default_id", _id(datos.idioma_default_id)),
                ("empresa_padre_id", _id(datos.empresa_padre_id)),
                ("ubicacion_geografica_id", _id(datos.ubicacion_geografica_id)),
            )
            if valor is not None
        }
        try:
            fila = empresas.actualizar_empresa(int(id), **campos)
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_empresa(fila)

    @strawberry.mutation(
        description="Soft delete: la fila queda, se le pone el estado "
        "Inactiva. Falla si tiene sucursales activas."
    )
    @solo_proveedor
    def desactivar_empresa(self, info: strawberry.Info, id: strawberry.ID) -> EmpresaType:
        try:
            fila = empresas.desactivar_empresa(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_empresa(fila)


@auto_permisos(recurso="CORE_EMPRESAS")
@strawberry.type
class EmpresaPaisMutations:
    @strawberry.mutation(
        description="Agrega un país donde opera la empresa, con sus datos de "
        "contacto."
    )
    @requiere_autenticacion
    @solo_proveedor
    def agregar_pais_a_empresa(
        self, info: strawberry.Info, datos: AgregarPaisInput
    ) -> EmpresaPaisType:
        try:
            fila = empresas.agregar_pais(
                empresa_id=int(datos.empresa_id),
                pais_id=int(datos.pais_id),
                ubicacion_geografica_id=_id(datos.ubicacion_geografica_id),
                direccion=datos.direccion,
                telefono=datos.telefono,
                email=datos.email,
                sitio_web=datos.sitio_web,
                logo=datos.logo,
                latitud=datos.latitud,
                longitud=datos.longitud,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return EmpresaPaisType.desde_modelo(fila)

    @strawberry.mutation(
        description="Los datos de contacto de la ficha de país: dirección, "
        "teléfono, correo, sitio web, logo y coordenadas. El país no se "
        "cambia; para eso se borra la ficha y se crea la del país nuevo."
    )
    @requiere_autenticacion
    @requiere_permiso
    def actualizar_pais_de_empresa(
        self,
        info: strawberry.Info,
        id: strawberry.ID,
        datos: ActualizarPaisDeEmpresaInput,
    ) -> EmpresaPaisType:
        campos = {
            campo: valor
            for campo, valor in (
                ("ubicacion_geografica_id", _id(datos.ubicacion_geografica_id)),
                ("direccion", datos.direccion),
                ("telefono", datos.telefono),
                ("email", datos.email),
                ("sitio_web", datos.sitio_web),
                ("logo", datos.logo),
                ("latitud", datos.latitud),
                ("longitud", datos.longitud),
            )
            if valor is not None
        }
        try:
            fila = empresas.actualizar_pais(int(id), **campos)
        except ValidationError as error:
            raise _traducir(error) from error
        return EmpresaPaisType.desde_modelo(fila)


@auto_permisos(recurso="CORE_EMPRESAS")
@strawberry.type
class EmpresaMonedaMutations:
    @strawberry.mutation(
        description="Habilita una moneda para una empresa. Si es la primera, "
        "queda como su moneda oficial: sin base de conversión no hay montoBase."
    )
    @requiere_autenticacion
    @requiere_permiso
    def agregar_moneda_a_empresa(
        self,
        info: strawberry.Info,
        moneda_id: strawberry.ID,
        es_moneda_oficial: bool = False,
    ) -> EmpresaMonedaType:
        try:
            fila = empresas.agregar_moneda(
                empresa_id=_empresa_de_la_sesion(),
                moneda_id=int(moneda_id),
                es_moneda_oficial=es_moneda_oficial,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return EmpresaMonedaType.desde_modelo(fila)

    @strawberry.mutation(
        description="Cambia la moneda base de una empresa. Desmarca la "
        "anterior, y solo la de ESA empresa. No reescribe documentos ya "
        "emitidos: cada uno guarda su montoBase."
    )
    @requiere_autenticacion
    @requiere_permiso
    def marcar_moneda_oficial(
        self, info: strawberry.Info, moneda_id: strawberry.ID
    ) -> EmpresaMonedaType:
        try:
            fila = empresas.marcar_moneda_oficial(
                _empresa_de_la_sesion(), int(moneda_id)
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return EmpresaMonedaType.desde_modelo(fila)

    @strawberry.mutation(
        description="Saca una moneda de las que opera la empresa. Soft "
        "delete. Rechaza la oficial: quedaría sin base de conversión."
    )
    @requiere_autenticacion
    @requiere_permiso
    def quitar_moneda_de_empresa(
        self, info: strawberry.Info, moneda_id: strawberry.ID
    ) -> bool:
        try:
            empresas.quitar_moneda(_empresa_de_la_sesion(), int(moneda_id))
        except ValidationError as error:
            raise _traducir(error) from error
        return True


@strawberry.type
class EmpresaMutation(EmpresaMutations, EmpresaPaisMutations, EmpresaMonedaMutations):
    """La superficie de escritura de empresas. Solo compone."""
