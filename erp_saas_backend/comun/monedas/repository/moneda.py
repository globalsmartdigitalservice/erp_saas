"""Acceso a datos de `Moneda`."""

from comun.monedas.models import Moneda


def obtener(moneda_id: int) -> Moneda | None:
    return Moneda.objects.filter(pk=moneda_id).first()


def obtener_varias(moneda_ids) -> dict[int, Moneda]:
    """
    Versión por lote. OBLIGATORIA.

    No es adorno: en el modelo de datos hay **25 tablas** con `monedaId`
    —documentos, cobros, pagos, asientos, planilla, cuentas bancarias—.
    Sin esto, cualquier listado que muestre la moneda de cada fila
    dispara una consulta por fila.
    """
    return {m.pk: m for m in Moneda.objects.filter(pk__in=list(moneda_ids))}


def listar(estado_id: int | None = None) -> list[Moneda]:
    """
    Todas las monedas, o las de un estado.

    Recibe el `estado_id` ya resuelto y no un booleano `solo_activas`:
    "activa" no es un valor que esta capa pueda conocer, porque el
    estado de `Moneda` es FK a `Tipologia`. Quien llama ya lo tiene.
    """
    qs = Moneda.objects.all()
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def obtener_por_codigo(codigo: str) -> Moneda | None:
    return Moneda.objects.filter(codigo=codigo).first()


def existe_codigo(codigo: str, excluir_id: int | None = None) -> bool:
    qs = Moneda.objects.filter(codigo=codigo)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(
    *,
    descripcion: str,
    codigo: str,
    simbolo: str = "",
    estado_id: int,
) -> Moneda:
    return Moneda.objects.create(
        descripcion=descripcion,
        codigo=codigo,
        simbolo=simbolo,
        estado_id=estado_id,
    )


def actualizar(moneda: Moneda, **campos) -> Moneda:
    for campo, valor in campos.items():
        setattr(moneda, campo, valor)
    moneda.save(update_fields=list(campos))
    return moneda
