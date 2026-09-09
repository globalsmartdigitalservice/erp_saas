"""Los tipos que ve el frontend. Sin lógica: solo forma."""

import datetime
import decimal

import strawberry

from comun.monedas.models import Moneda, TipoCambio
from comun.tipologias.graphql.types import TipologiaType


@strawberry.type(name="Moneda")
class MonedaType:
    id: strawberry.ID
    descripcion: str
    codigo: str
    simbolo: str


    estado: TipologiaType | None

    @classmethod
    def desde_modelo(
        cls, moneda: Moneda, estado: TipologiaType | None
    ) -> "MonedaType":
        return cls(
            id=strawberry.ID(str(moneda.pk)),
            descripcion=moneda.descripcion,
            codigo=moneda.codigo,
            simbolo=moneda.simbolo,
            estado=estado,
        )


@strawberry.type(name="TipoCambio")
class TipoCambioType:
    """
    Una cotización: un par de monedas, una fecha, un valor.

    Las DOS monedas viajan porque el valor solo no dice nada: "6.96" es
    6.96 **bolivianos por dólar**, y el mismo día en Perú son 3.75
    soles por dólar.

    El `id` viaja porque el documento que use esta tasa tiene que
    guardarlo (`tipoCambioId`) junto con el valor, para poder auditar
    después de dónde salió.

    NO expone `empresaId`: de quién es cada cotización no es asunto de
    nadie más, y de todas formas el manager solo devuelve las propias.
    """

    id: strawberry.ID
    moneda_origen_id: strawberry.ID
    moneda_destino_id: strawberry.ID
    fecha: datetime.date
    valor: decimal.Decimal
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, cotizacion: TipoCambio) -> "TipoCambioType":
        return cls(
            id=strawberry.ID(str(cotizacion.pk)),
            moneda_origen_id=strawberry.ID(str(cotizacion.moneda_origen_id)),
            moneda_destino_id=strawberry.ID(str(cotizacion.moneda_destino_id)),
            fecha=cotizacion.fecha,
            valor=cotizacion.valor,
            estado_id=strawberry.ID(str(cotizacion.estado_id)),
        )
