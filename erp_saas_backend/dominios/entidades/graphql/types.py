"""Los tipos de `entidades` que ve el frontend. Sin lógica: solo forma."""

import datetime
import decimal

import strawberry

from comun.tipologias.graphql.types import TipologiaType
from dominios.entidades.models import (
    CategoriaEntidad,
    ContactoEntidad,
    Direccion,
    EncuestaSatisfaccion,
    Entidad,
    RolEntidad,
)


@strawberry.type(name="CategoriaEntidad")
class CategoriaEntidadType:
    id: strawberry.ID
    nombre: str
    descripcion: str
    descuento_categ_cliente: decimal.Decimal

    # Entero suelto, no una relación: en el modelo de datos la línea a
    # `Lista_Precio` es punteada ("lista asignada [suave]") y esa tabla
    # es del módulo 05.1, que no está construido. Se expone el número
    # crudo en vez de inventar un tipo que no tiene tabla detrás.
    lista_precio_id: int | None
    estado: TipologiaType | None

    @classmethod
    def desde_modelo(
        cls,
        fila: CategoriaEntidad,
        estado: TipologiaType | None = None,
        nombre: str | None = None,
        descripcion: str | None = None,
    ) -> "CategoriaEntidadType":
        """
        `nombre` y `descripcion` llegan TRADUCIDOS, o no llegan.

        Mismo trato que `TipologiaType`: el que arma la lista ya trajo
        las traducciones por lote (ver `queries.py`), acá no se consulta
        nada. None = no hay traducción en el idioma activo y se muestra
        el texto tal como lo cargó el cliente.

         Solo se traducen estos dos campos, y es a propósito. El
        `nombre` de una `Entidad` NO se traduce: es el nombre de una
        persona o una empresa, no un texto de catálogo.
        """
        return cls(
            id=strawberry.ID(str(fila.pk)),
            nombre=nombre if nombre is not None else fila.nombre,
            descripcion=(
                descripcion if descripcion is not None else fila.descripcion
            ),
            descuento_categ_cliente=fila.descuento_categ_cliente,
            lista_precio_id=fila.lista_precio_id,
            estado=estado,
        )


@strawberry.type(name="RolEntidad")
class RolEntidadType:
    id: strawberry.ID
    entidad_id: strawberry.ID
    tipo_rol: TipologiaType | None
    categoria: CategoriaEntidadType | None
    limite_credito: decimal.Decimal | None
    datos_rol: strawberry.scalars.JSON
    estado: TipologiaType | None

    # ⏸ `vendedor` no está: el modelo de datos lo declara como FK a una tabla
    # `Vendedor` que no existe, y se confirmó que
    # es una segunda FK a `Entidad`, opcional, que se usa recién en
    # ventas. Ver models/rol_entidad.py.

    @classmethod
    def desde_modelo(
        cls,
        fila: RolEntidad,
        tipo_rol: TipologiaType | None,
        estado: TipologiaType | None,
        categoria: CategoriaEntidadType | None,
    ) -> "RolEntidadType":
        return cls(
            id=strawberry.ID(str(fila.pk)),
            entidad_id=strawberry.ID(str(fila.entidad_id)),
            tipo_rol=tipo_rol,
            categoria=categoria,
            limite_credito=fila.limite_credito,
            datos_rol=fila.datos_rol,
            estado=estado,
        )


@strawberry.type(name="Direccion")
class DireccionType:
    id: strawberry.ID
    entidad_id: strawberry.ID
    tipo: TipologiaType | None
    calle: str
    numero: str
    descripcion: str
    ubicacion_geografica_id: strawberry.ID | None
    direccion_texto: str
    latitud: decimal.Decimal | None
    longitud: decimal.Decimal | None
    estado: TipologiaType | None

    @classmethod
    def desde_modelo(
        cls,
        fila: Direccion,
        tipo: TipologiaType | None,
        estado: TipologiaType | None,
    ) -> "DireccionType":
        ubicacion = fila.ubicacion_geografica_id
        return cls(
            id=strawberry.ID(str(fila.pk)),
            entidad_id=strawberry.ID(str(fila.entidad_id)),
            tipo=tipo,
            calle=fila.calle,
            numero=fila.numero,
            descripcion=fila.descripcion,
            ubicacion_geografica_id=(
                strawberry.ID(str(ubicacion)) if ubicacion else None
            ),
            direccion_texto=fila.direccion_texto,
            latitud=fila.latitud,
            longitud=fila.longitud,
            estado=estado,
        )


@strawberry.type(name="ContactoEntidad")
class ContactoEntidadType:
    id: strawberry.ID
    entidad_id: strawberry.ID
    nombre: str
    cargo: str
    email: str
    telefono: str
    estado: TipologiaType | None

    @classmethod
    def desde_modelo(
        cls, fila: ContactoEntidad, estado: TipologiaType | None = None
    ) -> "ContactoEntidadType":
        return cls(
            id=strawberry.ID(str(fila.pk)),
            entidad_id=strawberry.ID(str(fila.entidad_id)),
            nombre=fila.nombre,
            cargo=fila.cargo,
            email=fila.email,
            telefono=fila.telefono,
            estado=estado,
        )


@strawberry.type(name="EncuestaSatisfaccion")
class EncuestaSatisfaccionType:
    id: strawberry.ID
    entidad_id: strawberry.ID
    fecha: datetime.date
    puntaje: int
    comentario: str

    @classmethod
    def desde_modelo(cls, fila: EncuestaSatisfaccion) -> "EncuestaSatisfaccionType":
        return cls(
            id=strawberry.ID(str(fila.pk)),
            entidad_id=strawberry.ID(str(fila.entidad_id)),
            fecha=fila.fecha,
            puntaje=fila.puntaje,
            comentario=fila.comentario,
        )


@strawberry.type(name="Entidad")
class EntidadType:
    id: strawberry.ID
    tipo_entidad: TipologiaType | None
    nombre: str
    pri_apellido: str
    seg_apellido: str
    tipo_documento: TipologiaType | None
    documento: str
    regimen_tributario: TipologiaType | None
    estado: TipologiaType | None

    # Vacías en la query de lista, llenas en `entidad(id)`. Ver el aviso
    # de la cabecera: no es un olvido, es la decisión de no hacer eager
    # cuatro colecciones que el cliente puede no haber pedido.
    roles: list[RolEntidadType]
    direcciones: list[DireccionType]
    contactos: list[ContactoEntidadType]
    encuestas: list[EncuestaSatisfaccionType]

    @classmethod
    def desde_modelo(
        cls,
        fila: Entidad,
        tipo_entidad: TipologiaType | None,
        tipo_documento: TipologiaType | None,
        regimen_tributario: TipologiaType | None,
        estado: TipologiaType | None,
        roles: list[RolEntidadType] | None = None,
        direcciones: list[DireccionType] | None = None,
        contactos: list[ContactoEntidadType] | None = None,
        encuestas: list[EncuestaSatisfaccionType] | None = None,
    ) -> "EntidadType":
        return cls(
            id=strawberry.ID(str(fila.pk)),
            tipo_entidad=tipo_entidad,
            nombre=fila.nombre,
            pri_apellido=fila.pri_apellido,
            seg_apellido=fila.seg_apellido,
            tipo_documento=tipo_documento,
            documento=fila.documento,
            regimen_tributario=regimen_tributario,
            estado=estado,
            roles=roles or [],
            direcciones=direcciones or [],
            contactos=contactos or [],
            encuestas=encuestas or [],
        )
