"""
Acceso a datos de `Referencia_Cruzada`. Filtrado por empresa (tenant).

Las dos consultas que existen de verdad son en direcciones opuestas:

    desde_origen()   "¿qué generó este pedido?"
    hacia_destino()  "¿de dónde viene esta factura?"

Las dos tienen su índice en el modelo.
"""

from servicios.integraciones.models import ReferenciaCruzada


def obtener(vinculo_id: int) -> ReferenciaCruzada | None:
    return ReferenciaCruzada.objects.filter(pk=vinculo_id).first()


def obtener_varios(vinculo_ids) -> dict[int, ReferenciaCruzada]:
    return {
        v.pk: v for v in ReferenciaCruzada.objects.filter(pk__in=list(vinculo_ids))
    }


def desde_origen(tabla: str, registro_id: int) -> list[ReferenciaCruzada]:
    """Lo que este registro generó."""
    return list(
        ReferenciaCruzada.objects.filter(
            tabla_origen=tabla, registro_origen_id=registro_id
        ).order_by("-creado_en")
    )


def hacia_destino(tabla: str, registro_id: int) -> list[ReferenciaCruzada]:
    """De dónde viene este registro."""
    return list(
        ReferenciaCruzada.objects.filter(
            tabla_destino=tabla, registro_destino_id=registro_id
        ).order_by("-creado_en")
    )


def existe(
    *,
    tabla_origen: str,
    registro_origen_id: int,
    tabla_destino: str,
    registro_destino_id: int,
    tipo_vinculo_id: int,
) -> bool:
    return ReferenciaCruzada.objects.filter(
        tabla_origen=tabla_origen,
        registro_origen_id=registro_origen_id,
        tabla_destino=tabla_destino,
        registro_destino_id=registro_destino_id,
        tipo_vinculo_id=tipo_vinculo_id,
    ).exists()


def crear(**campos) -> ReferenciaCruzada:
    return ReferenciaCruzada.objects.create(**campos)


def actualizar(fila: ReferenciaCruzada, **campos) -> ReferenciaCruzada:
    for campo, valor in campos.items():
        setattr(fila, campo, valor)
    fila.save(update_fields=list(campos))
    return fila
