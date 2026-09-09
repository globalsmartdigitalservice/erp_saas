

from contextlib import contextmanager
from contextvars import ContextVar

_idioma: ContextVar[int | None] = ContextVar("idioma_actual", default=None)


def idioma_actual() -> int | None:
    """
    El id del idioma activo, o None si no se fijó ninguno.

    None significa "mostrá los textos como están guardados", no "error".
    """
    return _idioma.get()


def hay_idioma() -> bool:
    return _idioma.get() is not None


def establecer_idioma(idioma_id: int):
    """
    Fija el idioma activo. Devuelve un token para restaurar el valor
    anterior con `restaurar_idioma`. Lo usa el middleware.
    """
    return _idioma.set(idioma_id)


def restaurar_idioma(token) -> None:
    _idioma.reset(token)


@contextmanager
def idioma(idioma_id: int | None):
    """
    Fija el idioma dentro de un bloque y lo restaura al salir.

        with idioma(ingles.pk):
            ...

    Para tareas en segundo plano, comandos y tests. Acepta None para
    poder apagarlo explícitamente dentro de un bloque.
    """
    token = _idioma.set(idioma_id)
    try:
        yield
    finally:
        _idioma.reset(token)
