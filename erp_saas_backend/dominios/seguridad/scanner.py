"""Dónde buscar las mutations decoradas.

Se recorren las apps de `INSTALLED_APPS` y se intenta importar su
`graphql/mutations.py`. La que no lo tenga se saltea sin ruido.

 Se recorren las apps y no una lista en settings porque una lista es un
lugar más donde olvidarse de anotar la app nueva — y ese olvido no da
error, deja la acción sin proteger."""

import importlib
import inspect

from django.apps import apps

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


def clases_con_permisos(stdout=None) -> list[type]:
    """Solo las decoradas, a nivel de clase o de algún método: así no se
    arrastran mutations que todavía no decidieron su permiso."""
    from dominios.seguridad.permisos import METADATA

    encontradas = []

    for config in apps.get_app_configs():
        if not config.name.startswith(PREFIJOS_DEL_PROYECTO):
            continue

        try:
            modulo = importlib.import_module(f"{config.name}.graphql.mutations")
        except ModuleNotFoundError:
            # La app no expone mutations. Es lo normal.
            continue
        except Exception as error:  # pragma: no cover - defensivo
            # Un error de import SÍ se avisa: si se lo tragara, esa app
            # quedaría sin permisos y nadie se enteraría.
            if stdout is not None:
                stdout.write(
                    f"  aviso: No se pudo leer {config.name}.graphql.mutations: {error}"
                )
            continue

        for _, clase in inspect.getmembers(modulo, inspect.isclass):
            if clase.__module__ != modulo.__name__:
                # Importada de otro lado; se escanea donde vive.
                continue
            decorada_la_clase = hasattr(clase, "_auto_permiso_clase")
            decorado_un_metodo = any(
                hasattr(m, METADATA)
                for _, m in inspect.getmembers(clase, inspect.isfunction)
            )
            if decorada_la_clase or decorado_un_metodo:
                encontradas.append(clase)

    return encontradas


__all__ = ["clases_con_permisos", "PREFIJOS_DEL_PROYECTO"]
