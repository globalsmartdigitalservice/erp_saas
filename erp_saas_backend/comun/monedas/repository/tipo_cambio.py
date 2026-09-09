"""
Acceso a datos de `TipoCambio`.

Todas las consultas van por el manager de `ModeloTenant`, así que el
`WHERE empresa_id = ...` no se escribe acá: se aplica solo. Una empresa
no puede ver el historial de otra ni por error.

 Las búsquedas llevan `estado_id` como parámetro en vez de resolver
"lo activo" por su cuenta. El estado es una FK a `Tipologia`, así que
"activo" es una FILA que hay que buscar, y buscarla en cada consulta
sería una consulta de más por cada cotización pedida. La resuelve el
service, una vez.
"""

import datetime

from comun.monedas.models import TipoCambio


def obtener(tipo_cambio_id: int) -> TipoCambio | None:
    return TipoCambio.objects.filter(pk=tipo_cambio_id).first()


def obtener_varios(ids) -> dict[int, TipoCambio]:
    """Versión por lote. OBLIGATORIA — 11 tablas guardan `tipoCambioId`."""
    return {t.pk: t for t in TipoCambio.objects.filter(pk__in=list(ids))}


def obtener_vigente(
    *,
    moneda_origen_id: int,
    moneda_destino_id: int,
    fecha: datetime.date,
    estado_id: int,
) -> TipoCambio | None:
    """
    La cotización que RIGE en esa fecha: la última cargada con fecha
    menor o igual, para ese par de monedas.

    No es `fecha exacta` a propósito. Nadie carga cotización el sábado,
    el domingo ni el feriado, así que una búsqueda exacta devolvería
    nada justo cuando alguien factura con fecha de fin de semana. Con
    esto, el viernes cubre el sábado y el domingo.

    Devuelve la FILA entera, no el número: el documento tiene que
    congelar `tipoCambioId` y `valorTipoCambio` juntos.
    """
    return (
        TipoCambio.objects.filter(
            moneda_origen_id=moneda_origen_id,
            moneda_destino_id=moneda_destino_id,
            fecha__lte=fecha,
            estado_id=estado_id,
        )
        .order_by("-fecha")
        .first()
    )


def existe(
    *, moneda_origen_id: int, moneda_destino_id: int, fecha: datetime.date
) -> bool:
    """
    Contra la constraint única (empresa, origen, destino, fecha).

    NO filtra por estado: una cotización anulada sigue ocupando el lugar
    en la constraint, así que si acá se la ignorara saltaría un
    IntegrityError en vez de un mensaje entendible.
    """
    return TipoCambio.objects.filter(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        fecha=fecha,
    ).exists()


def listar(
    *,
    moneda_origen_id: int,
    moneda_destino_id: int,
    desde: datetime.date | None = None,
    hasta: datetime.date | None = None,
    estado_id: int | None = None,
) -> list[TipoCambio]:
    """El historial de un par, de la más nueva a la más vieja."""
    qs = TipoCambio.objects.filter(
        moneda_origen_id=moneda_origen_id, moneda_destino_id=moneda_destino_id
    )
    if desde is not None:
        qs = qs.filter(fecha__gte=desde)
    if hasta is not None:
        qs = qs.filter(fecha__lte=hasta)
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs.order_by("-fecha"))


def crear(
    *,
    moneda_origen_id: int,
    moneda_destino_id: int,
    fecha: datetime.date,
    valor,
    estado_id: int,
) -> TipoCambio:
    """
    La empresa NO se pasa: la pone `ModeloTenant.save()` desde el
    contexto. Si se pudiera pasar, se podría cargar una cotización en la
    empresa de otro.
    """
    return TipoCambio.objects.create(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        fecha=fecha,
        valor=valor,
        estado_id=estado_id,
    )


def actualizar(tipo_cambio: TipoCambio, **campos) -> TipoCambio:
    for campo, valor in campos.items():
        setattr(tipo_cambio, campo, valor)
    tipo_cambio.save(update_fields=list(campos))
    return tipo_cambio
