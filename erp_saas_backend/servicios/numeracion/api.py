"""
Superficie pública de `numeracion`. El resto de la app es privado.

    from servicios.numeracion import api as numeracion

    with atomic():
        numero = numeracion.siguiente_numero(serie_id, gestion=2026)
        ...  # emitir el documento

 `siguiente_numero()` SE LLAMA DENTRO DE LA TRANSACCIÓN QUE EMITE EL
DOCUMENTO, no antes. Es lo que hace que un documento fallido devuelva su
número en vez de dejar un hueco — la razón entera por la que esta tabla
no es una `SEQUENCE`.

Llamarla suelta CONSUME un número. Para mostrar sin consumir:
`numero_actual()`.
"""

from servicios.numeracion.models import Correlativo, SerieDocumental
from servicios.numeracion.repository import correlativo as _repo_correlativo
from servicios.numeracion.repository import serie_documental as _repo_serie
from servicios.numeracion.services import correlativo as _svc_correlativo
from servicios.numeracion.services import serie_documental as _svc_serie


def siguiente_numero(serie_id: int, gestion: int) -> int:
    """Toma el próximo número de la serie. Con lock. Ver el aviso de arriba."""
    return _svc_correlativo.siguiente_numero(serie_id, gestion)


def numero_actual(serie_id: int, gestion: int) -> int:
    """El último entregado, sin consumir ni bloquear. Para mostrar."""
    return _svc_correlativo.numero_actual(serie_id, gestion)


def formatear(serie_id: int, numero: int, ancho: int = 6) -> str:
    """El número como se imprime: `FAC-000123`."""
    return _svc_correlativo.formatear(serie_id, numero, ancho)


def obtener_serie(serie_id: int) -> SerieDocumental | None:
    return _repo_serie.obtener(serie_id)


def obtener_series(serie_ids) -> dict[int, SerieDocumental]:
    return _repo_serie.obtener_varias(serie_ids)


def listar_series() -> list[SerieDocumental]:
    return _repo_serie.listar()


def listar_series_de_tipo(tipo_documento_id: int) -> list[SerieDocumental]:
    return _repo_serie.listar_de_tipo(tipo_documento_id)


def crear_serie(**campos) -> SerieDocumental:
    return _svc_serie.crear(**campos)


def actualizar_serie(serie_id: int, **campos) -> SerieDocumental:
    return _svc_serie.actualizar(serie_id, **campos)


def desactivar_serie(serie_id: int) -> SerieDocumental:
    return _svc_serie.desactivar(serie_id)


def listar_correlativos_de(serie_id: int) -> list[Correlativo]:
    """
    El histórico por gestión. Para mostrar en pantalla.

     No hay `crear_correlativo` ni `actualizar_correlativo`, y no es un
    olvido: el único que escribe esa tabla es `siguiente_numero()`, con el
    lock tomado. Cualquier otra escritura rompe la numeración.
    """
    return _repo_correlativo.listar_de_serie(serie_id)
