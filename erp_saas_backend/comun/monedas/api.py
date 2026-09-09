"""Superficie pública de `monedas`. El resto de la app es privado.

    from comun.monedas import api as monedas

    dolar = monedas.obtener_por_codigo("USD")
    tasa  = monedas.cotizacion(
        moneda_origen_id=dolar.pk,
        moneda_destino_id=empresa_bob.pk,
        fecha=fecha_del_documento,
    )

 La versión por lote pesa acá más que en otras apps: el modelo de datos
tiene **25 tablas con `monedaId`** y **11 con `tipoCambioId`**, así que sin
ella cada listado de documentos dispara una consulta por fila.

Las lecturas van directo al repository; las escrituras pasan por services.
"""

import datetime

from comun.monedas.models import Moneda, TipoCambio
from comun.monedas.repository import moneda as _repo_moneda
from comun.monedas.repository import tipo_cambio as _repo_cambio
from comun.monedas.services import moneda as _svc_moneda
from comun.monedas.services import tipo_cambio as _svc_cambio


def obtener_moneda(moneda_id: int) -> Moneda | None:
    return _repo_moneda.obtener(moneda_id)


def obtener_monedas(moneda_ids) -> dict[int, Moneda]:
    return _repo_moneda.obtener_varias(moneda_ids)


def listar_monedas(estado_id: int | None = None) -> list[Moneda]:
    """
    Todas las monedas, o las de un estado.

    No lleva un `solo_activas=True` como `tipologias.de()`: el estado de
    `Moneda` es FK a `Tipologia`, así que "activa" es una FILA que hay
    que resolver antes, no un valor que esta capa pueda conocer. Quien
    arma un combo ya trae los estados por lote y filtra con eso.
    """
    return _repo_moneda.listar(estado_id)


def obtener_por_codigo(codigo: str) -> Moneda | None:
    """Por su código ISO. Para las integraciones, que hablan en códigos."""
    return _repo_moneda.obtener_por_codigo((codigo or "").strip().upper())


# NO EXISTE `moneda_oficial()`, Y NO VUELVE.
#
# Era "la moneda base del sistema", un dato global — y el modelo de datos ya no lo tiene
# porque en un SaaS no existe tal cosa: cada empresa tiene la suya. Se
# pide con `empresas.moneda_oficial_de(empresa_id)`.


def crear_moneda(
    *,
    descripcion: str,
    codigo: str,
    simbolo: str = "",
    estado_id: int,
) -> Moneda:
    """
    Alta en el CATÁLOGO. Que una empresa la use es otra cosa, y va por
    `empresas.agregar_moneda()`.
    """
    return _svc_moneda.crear(
        descripcion=descripcion,
        codigo=codigo,
        simbolo=simbolo,
        estado_id=estado_id,
    )


def actualizar_moneda(moneda_id: int, **campos) -> Moneda:
    return _svc_moneda.actualizar(moneda_id, **campos)


def desactivar_moneda(moneda_id: int) -> Moneda:
    return _svc_moneda.desactivar(moneda_id)


def cotizacion(
    *, moneda_origen_id: int, moneda_destino_id: int, fecha: datetime.date
) -> TipoCambio | None:
    """
    La cotización VIGENTE en esa fecha para ese par, EN LA EMPRESA
    ACTIVA: la última cargada con fecha menor o igual.

    Es la que consume todo documento en moneda extranjera. Devuelve la
    fila entera porque el documento tiene que guardar las dos cosas:
    `tipoCambioId` (de dónde salió) y `valorTipoCambio` (qué se usó).

    Van las DOS monedas porque el valor no significa nada sin saber en
    qué está expresado: "el dólar a 6.96" es 6.96 **bolivianos**, y en
    Perú el mismo día son 3.75 soles.

    Devuelve None si ese par nunca tuvo cotización cargada en esta
    empresa. Las anuladas no cuentan.
    """
    return _svc_cambio.vigente(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        fecha=fecha,
    )


def obtener_cotizacion(tipo_cambio_id: int) -> TipoCambio | None:
    return _repo_cambio.obtener(tipo_cambio_id)


def obtener_cotizaciones(ids) -> dict[int, TipoCambio]:
    return _repo_cambio.obtener_varios(ids)


def cotizaciones(
    *,
    moneda_origen_id: int,
    moneda_destino_id: int,
    desde: datetime.date | None = None,
    hasta: datetime.date | None = None,
    incluir_anuladas: bool = False,
) -> list[TipoCambio]:
    """El historial de un par, de la más nueva a la más vieja."""
    return _svc_cambio.historial(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        desde=desde,
        hasta=hasta,
        incluir_anuladas=incluir_anuladas,
    )


def registrar_cotizacion(
    *,
    moneda_origen_id: int,
    moneda_destino_id: int,
    fecha: datetime.date,
    valor,
) -> TipoCambio:
    """
    Carga una cotización EN LA EMPRESA ACTIVA.

    No recibe `empresa_id` y nunca lo va a recibir: sale del contexto.
    """
    return _svc_cambio.registrar(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        fecha=fecha,
        valor=valor,
    )


def corregir_cotizacion(tipo_cambio_id: int, valor) -> TipoCambio:
    """
    Corrige el VALOR de una cotización mal cargada. Para el dedazo.

    Distinto de `anular_cotizacion`: acá la cotización tenía que
    existir y el número estaba mal.
    """
    return _svc_cambio.corregir(tipo_cambio_id, valor)


def anular_cotizacion(tipo_cambio_id: int) -> TipoCambio:
    """
    Soft delete de una cotización que no tendría que existir.

    La fila NO se borra: si un documento la usó, su `tipoCambioId` sigue
    apuntando a algo y la auditoría no se rompe. Solo deja de
    sugerirse. Es lo que habilitó el `estadoId` del modelo de datos.
    """
    return _svc_cambio.anular(tipo_cambio_id)


__all__ = [
    "obtener_moneda",
    "obtener_monedas",
    "listar_monedas",
    "obtener_por_codigo",
    "crear_moneda",
    "actualizar_moneda",
    "desactivar_moneda",
    "cotizacion",
    "obtener_cotizacion",
    "obtener_cotizaciones",
    "cotizaciones",
    "registrar_cotizacion",
    "corregir_cotizacion",
    "anular_cotizacion",
]
