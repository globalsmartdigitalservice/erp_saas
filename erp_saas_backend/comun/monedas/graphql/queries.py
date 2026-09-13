"""Las consultas de monedas."""

import datetime

import strawberry

from comun.monedas import api as monedas
from comun.tipologias import api as tipologias
from comun.tipologias.graphql.types import TipologiaType

from dominios.seguridad.permisos_graphql import requiere_autenticacion

from .types import MonedaType, TipoCambioType


def _resolver_estados(filas):
    """
    Trae de una sola consulta el estado de todas las filas.

    Este es el batch a mano del que depende no tener N+1: se juntan
    todos los `estado_id` y se piden juntos por el `api.py` de
    tipologias.
    """
    estados = tipologias.obtener_varias({f.estado_id for f in filas})
    return {
        id_: TipologiaType.desde_modelo(tipologia)
        for id_, tipologia in estados.items()
    }


@strawberry.type
class MonedaQueries:
    @strawberry.field(description="Todas las monedas del sistema.")
    def monedas(self) -> list[MonedaType]:
        filas = monedas.listar_monedas()
        estados = _resolver_estados(filas)
        return [MonedaType.desde_modelo(m, estados.get(m.estado_id)) for m in filas]

    @strawberry.field(description="Una moneda por su id.")
    def moneda(self, id: strawberry.ID) -> MonedaType | None:
        fila = monedas.obtener_moneda(int(id))
        if fila is None:
            return None
        estados = _resolver_estados([fila])
        return MonedaType.desde_modelo(fila, estados.get(fila.estado_id))


@strawberry.type
class CotizacionQueries:
    @strawberry.field(
        description="La cotización VIGENTE en esa fecha para ese par de "
        "monedas: la última cargada con fecha menor o igual. Un domingo "
        "devuelve la del viernes. Solo las de la empresa activa, y las "
        "anuladas no cuentan."
    )
    @requiere_autenticacion
    def cotizacion(
        self,
        info: strawberry.Info,
        moneda_origen_id: strawberry.ID,
        moneda_destino_id: strawberry.ID,
        fecha: datetime.date,
    ) -> TipoCambioType | None:
        fila = monedas.cotizacion(
            moneda_origen_id=int(moneda_origen_id),
            moneda_destino_id=int(moneda_destino_id),
            fecha=fecha,
        )
        return TipoCambioType.desde_modelo(fila) if fila else None

    @strawberry.field(
        description="El historial de cotizaciones de un par de monedas, de "
        "la más nueva a la más vieja."
    )
    @requiere_autenticacion
    def cotizaciones(
        self,
        info: strawberry.Info,
        moneda_origen_id: strawberry.ID,
        moneda_destino_id: strawberry.ID,
        desde: datetime.date | None = None,
        hasta: datetime.date | None = None,
        incluir_anuladas: bool = False,
    ) -> list[TipoCambioType]:
        filas = monedas.cotizaciones(
            moneda_origen_id=int(moneda_origen_id),
            moneda_destino_id=int(moneda_destino_id),
            desde=desde,
            hasta=hasta,
            incluir_anuladas=incluir_anuladas,
        )
        return [TipoCambioType.desde_modelo(c) for c in filas]


@strawberry.type
class MonedaQuery(MonedaQueries, CotizacionQueries):
    """La superficie de consulta de monedas. Solo compone."""
