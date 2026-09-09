"""Los inputs de las mutations."""

import datetime
import decimal

import strawberry


@strawberry.input
class CrearMonedaInput:
    descripcion: str
    codigo: str
    estado_id: strawberry.ID
    simbolo: str = ""


@strawberry.input
class ActualizarMonedaInput:
    descripcion: str | None = None
    codigo: str | None = None
    simbolo: str | None = None
    estado_id: strawberry.ID | None = None


@strawberry.input
class RegistrarCotizacionInput:

    moneda_origen_id: strawberry.ID
    moneda_destino_id: strawberry.ID
    fecha: datetime.date
    valor: decimal.Decimal
