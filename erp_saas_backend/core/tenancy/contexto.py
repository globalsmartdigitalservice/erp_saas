"""
La "cajita" que guarda qué empresa está trabajando en este momento.

Se llena una sola vez por request (desde el token)
y la leen los managers para filtrar cada consulta.

Por qué ContextVar y no una variable global ni un thread-local:
el servidor es ASGI (Uvicorn) y un mismo hilo atiende varias requests
a la vez. Con un thread-local, la empresa de un usuario se le
mezclaría a otro — exactamente la fuga que todo esto evita.
ContextVar aísla el valor por tarea asíncrona.
"""

from contextlib import contextmanager
from contextvars import ContextVar


_empresa: ContextVar[int | None] = ContextVar("empresa_actual", default=None)
_sin_filtro: ContextVar[bool] = ContextVar("sin_filtro_empresa", default=False)


class SinEmpresaEnContexto(RuntimeError):
    """
    Se consultó una tabla con empresa sin que hubiera empresa activa.

    Se prefiere reventar antes que devolver una lista vacía: un listado
    vacío se confunde con "esta empresa no tiene datos" y puede costar
    días encontrarlo. Un error se ve en el momento.
    """


def empresa_actual() -> int | None:
    """El id de la empresa activa, o None si no hay ninguna."""
    return _empresa.get()


def hay_empresa() -> bool:
    return _empresa.get() is not None


def filtro_desactivado() -> bool:
    return _sin_filtro.get()


def establecer_empresa(empresa_id: int):
    """
    Fija la empresa activa. Devuelve un token para poder restaurar
    el valor anterior con `restaurar_empresa`.

    Lo usa el middleware, una vez por request.
    """
    return _empresa.set(empresa_id)


def restaurar_empresa(token) -> None:
    _empresa.reset(token)


@contextmanager
def empresa(empresa_id: int):
    """
    Fija la empresa dentro de un bloque y la restaura al salir.

        with empresa(7):
            Venta.objects.all()      # solo las de la empresa 7

    Para tareas en segundo plano, comandos y tests — donde no hay
    request que llene la cajita.
    """
    token = _empresa.set(empresa_id)
    try:
        yield
    finally:
        _empresa.reset(token)


@contextmanager
def sin_filtro_de_empresa():
    """
    Apaga el filtro automático dentro del bloque.

        with sin_filtro_de_empresa():
            Empresa.objects.all()    # todas, a propósito

    Es la puerta de salida para lo que legítimamente cruza empresas:
    el panel del proveedor, comandos de management, migraciones.

    Si aparece dentro de `dominios/`, hay algo mal: ahí nunca
    debería usarse.
    """
    token = _sin_filtro.set(True)
    try:
        yield
    finally:
        _sin_filtro.reset(token)
