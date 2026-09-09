"""Los inputs de las mutations de entidades."""

import datetime
import decimal

import strawberry


@strawberry.input
class CrearEntidadInput:
    tipo_entidad_id: strawberry.ID
    nombre: str
    tipo_documento_id: strawberry.ID
    estado_id: strawberry.ID
    pri_apellido: str = ""
    seg_apellido: str = ""
    documento: str = ""
    regimen_tributario_id: strawberry.ID | None = None


@strawberry.input
class ActualizarEntidadInput:
    tipo_entidad_id: strawberry.ID | None = None
    nombre: str | None = None
    pri_apellido: str | None = None
    seg_apellido: str | None = None
    tipo_documento_id: strawberry.ID | None = None
    documento: str | None = None
    regimen_tributario_id: strawberry.ID | None = None
    estado_id: strawberry.ID | None = None


@strawberry.input
class CrearCategoriaEntidadInput:
    nombre: str
    estado_id: strawberry.ID
    descripcion: str = ""
    descuento_categ_cliente: decimal.Decimal = decimal.Decimal("0")
    # Entero suelto a propósito: `Lista_Precio` es del módulo 05.1 y no
    # existe. Ver el comentario en el modelo.
    lista_precio_id: int | None = None


@strawberry.input
class ActualizarCategoriaEntidadInput:
    nombre: str | None = None
    descripcion: str | None = None
    descuento_categ_cliente: decimal.Decimal | None = None
    lista_precio_id: int | None = None
    estado_id: strawberry.ID | None = None


@strawberry.input
class CrearRolEntidadInput:
    entidad_id: strawberry.ID
    tipo_rol_id: strawberry.ID
    estado_id: strawberry.ID
    categoria_entidad_id: strawberry.ID | None = None
    limite_credito: decimal.Decimal | None = None
    datos_rol: strawberry.scalars.JSON | None = None


@strawberry.input
class ActualizarRolEntidadInput:
    # `entidad_id` y `tipo_rol_id` NO están: son lo que ese rol ES.
    # Cambiar cualquiera de los dos es borrar este rol y crear otro.
    categoria_entidad_id: strawberry.ID | None = None
    limite_credito: decimal.Decimal | None = None
    datos_rol: strawberry.scalars.JSON | None = None
    estado_id: strawberry.ID | None = None


@strawberry.input
class CrearDireccionInput:
    entidad_id: strawberry.ID
    tipo_id: strawberry.ID
    estado_id: strawberry.ID
    calle: str = ""
    numero: str = ""
    descripcion: str = ""
    ubicacion_geografica_id: strawberry.ID | None = None
    direccion_texto: str = ""
    latitud: decimal.Decimal | None = None
    longitud: decimal.Decimal | None = None


@strawberry.input
class ActualizarDireccionInput:
    tipo_id: strawberry.ID | None = None
    calle: str | None = None
    numero: str | None = None
    descripcion: str | None = None
    ubicacion_geografica_id: strawberry.ID | None = None
    direccion_texto: str | None = None
    latitud: decimal.Decimal | None = None
    longitud: decimal.Decimal | None = None
    estado_id: strawberry.ID | None = None


@strawberry.input
class CrearContactoEntidadInput:
    entidad_id: strawberry.ID
    nombre: str
    estado_id: strawberry.ID
    cargo: str = ""
    email: str = ""
    telefono: str = ""


@strawberry.input
class ActualizarContactoEntidadInput:
    nombre: str | None = None
    cargo: str | None = None
    email: str | None = None
    telefono: str | None = None
    estado_id: strawberry.ID | None = None


@strawberry.input
class RegistrarEncuestaInput:
    entidad_id: strawberry.ID
    fecha: datetime.date
    puntaje: int
    comentario: str = ""
