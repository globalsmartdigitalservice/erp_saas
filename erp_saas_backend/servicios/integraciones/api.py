"""
Superficie pública de `integraciones`.

    from servicios.integraciones import api as integraciones

    integraciones.vincular(
        modulo_origen="VENTAS",  tabla_origen="vent_pedido",     registro_origen_id=7,
        modulo_destino="VENTAS", tabla_destino="vent_documento", registro_destino_id=12,
        tipo_vinculo_id=genera.pk, estado_id=activo.pk,
    )

    integraciones.que_genero("vent_pedido", 7)           # hacia adelante
    integraciones.de_donde_viene("vent_documento", 12)   # hacia atrás
"""

from servicios.integraciones.models import ReferenciaCruzada
from servicios.integraciones.repository import referencia_cruzada as _repo
from servicios.integraciones.services import referencia_cruzada as _svc


def obtener(vinculo_id: int) -> ReferenciaCruzada | None:
    return _repo.obtener(vinculo_id)


def obtener_varios(vinculo_ids) -> dict[int, ReferenciaCruzada]:
    return _repo.obtener_varios(vinculo_ids)


def que_genero(tabla: str, registro_id: int) -> list[ReferenciaCruzada]:
    """Lo que este registro produjo. Tiene índice propio."""
    return _repo.desde_origen(tabla, registro_id)


def de_donde_viene(tabla: str, registro_id: int) -> list[ReferenciaCruzada]:
    """De qué salió este registro. Tiene índice propio."""
    return _repo.hacia_destino(tabla, registro_id)


def vincular(**campos) -> ReferenciaCruzada:
    return _svc.vincular(**campos)


def anular(vinculo_id: int) -> ReferenciaCruzada:
    """Soft delete: un vínculo anulado sigue siendo historia."""
    return _svc.anular(vinculo_id)
