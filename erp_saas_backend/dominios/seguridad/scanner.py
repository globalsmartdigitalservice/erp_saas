"""Dónde buscar las operaciones decoradas.

Se recorren las apps de `INSTALLED_APPS` y se intenta importar su
`graphql/mutations.py` y su `graphql/queries.py`. La que no los tenga se
saltea sin ruido.

 Se recorren las apps y no una lista en settings porque una lista es un
lugar más donde olvidarse de anotar la app nueva — y ese olvido no da
error, deja la acción sin proteger."""

import importlib
import inspect

from django.apps import apps

MODULOS_DE_GRAPHQL = ("mutations", "queries")

# Las mismas capas que ya usa la red de seguridad para saber qué es
# nuestro y qué viene de terceros.
PREFIJOS_DEL_PROYECTO = (
    "comun",
    "core",
    "servicios",
    "dominios",
    "procesos",
    "proveedor",
    "complementos",
)


def _declara_permisos(clase) -> bool:
    """¿La clase declara permisos ELLA MISMA, o solo los hereda?

    Se mira `__dict__` y no `hasattr`, que sigue la herencia. Las clases que
    solo componen —`GeografiaMutation(PaisMutations, UbicacionMutations)`—
    heredan la marca de su primera base, así que con `hasattr` generarían los
    permisos de TODOS sus métodos bajo el recurso de esa base: `crear_ubicacion`
    quedaría además como `core_paises_crear_ubicacion`.

    Y ese permiso de más no sobra, está muerto: `@requiere_permiso` deduce el
    código de la clase donde el método está DEFINIDO. Asignarlo a un rol no
    habilita nada, y nadie se entera. El escáner tiene que mirar la misma clase
    que mira el guard."""
    from dominios.seguridad.permisos import METADATA

    if "_auto_permiso_clase" in clase.__dict__:
        return True

    return any(
        hasattr(miembro, METADATA)
        for miembro in clase.__dict__.values()
        if inspect.isfunction(miembro)
    )


def clases_con_permisos(stdout=None) -> list[type]:
    """Solo las decoradas, a nivel de clase o de algún método: así no se
    arrastran operaciones que todavía no decidieron su permiso."""
    encontradas = []

    for config in apps.get_app_configs():
        if not config.name.startswith(PREFIJOS_DEL_PROYECTO):
            continue

        for nombre in MODULOS_DE_GRAPHQL:
            modulo = _importar(f"{config.name}.graphql.{nombre}", stdout)
            if modulo is None:
                continue

            for _, clase in inspect.getmembers(modulo, inspect.isclass):
                if clase.__module__ != modulo.__name__:
                    # Importada de otro lado; se escanea donde vive.
                    continue
                if _declara_permisos(clase):
                    encontradas.append(clase)

    return encontradas


def _importar(ruta: str, stdout):
    """El módulo, o `None` si la app no lo tiene."""
    try:
        return importlib.import_module(ruta)
    except ModuleNotFoundError:
        # La app no expone esa mitad de su esquema. Es lo normal.
        return None
    except Exception as error:  # pragma: no cover - defensivo
        # Un error de import SÍ se avisa: si se lo tragara, esa app
        # quedaría sin permisos y nadie se enteraría.
        if stdout is not None:
            stdout.write(f"  aviso: No se pudo leer {ruta}: {error}")
        return None


__all__ = ["clases_con_permisos", "PREFIJOS_DEL_PROYECTO", "MODULOS_DE_GRAPHQL"]
