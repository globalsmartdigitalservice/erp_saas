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
    arrastran mutations que todavía no decidieron su permiso."""
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
            if _declara_permisos(clase):
                encontradas.append(clase)

    return encontradas


__all__ = ["clases_con_permisos", "PREFIJOS_DEL_PROYECTO"]
