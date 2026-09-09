"""El decorador que marca qué permiso necesita cada mutation, y el escaneo
que arma el catálogo a partir de ellos.

Se escanea en vez de escribirlos a mano porque son más de 1.200 permisos:
escritos a mano se desincronizan el primer día y alguna acción queda sin
proteger. `recurso` es el `codigo` de un `Sub_Modulo`, que es el
identificador ESTABLE — `nombre` y `ruta` cambian.

Los permisos obsoletos NO se borran, se informan: borrar un
`auth_permission` le saca capacidades en silencio a todos los roles que
lo tenían."""

import functools
import inspect

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured

METADATA = "_auto_permiso"

_IGNORADOS = {"resolve_reference", "is_type_of"}


def auto_permisos(recurso: str, *, operacion: str | None = None, descripcion: str = ""):
    """Marca una clase de mutations o un método suelto.

    Sobre una CLASE se escanean todos sus métodos públicos. Sobre un MÉTODO
    gana sobre lo que diga la clase."""
    if not recurso or not recurso.strip():
        raise ImproperlyConfigured(
            "@auto_permisos necesita un `recurso`: es el `codigo` del "
            "Sub_Modulo (la pantalla) al que pertenece la acción."
        )

    def decorar(objetivo):
        if isinstance(objetivo, type):
            objetivo._auto_permiso_clase = {"recurso": recurso.strip().upper()}
            return objetivo

        setattr(
            objetivo,
            METADATA,
            {
                "recurso": recurso.strip().upper(),
                "operacion": (operacion or objetivo.__name__).strip().lower(),
                "descripcion": descripcion,
            },
        )

        @functools.wraps(objetivo)
        def envoltura(*args, **kwargs):
            return objetivo(*args, **kwargs)

        # La metadata también en la envoltura: `inspect` ve esta, no la
        # original.
        setattr(envoltura, METADATA, getattr(objetivo, METADATA))
        return envoltura

    return decorar


def codename_de(recurso: str, operacion: str) -> str:
    """El recurso va DENTRO del codename y no solo en el prefijo:
    `anular_factura` a secas chocaría entre ventas y compras."""
    return f"{recurso.lower()}_{operacion.lower()}"


def content_type_del_ancla() -> ContentType:
    """NO usa `get_for_model()`: ese cachea en memoria y el caché sobrevive
    a un rollback, así que los permisos quedarían apuntando a un ContentType
    que ya no existe."""
    from dominios.seguridad.models import PermisoDeNegocio

    meta = PermisoDeNegocio._meta
    tipo, _ = ContentType.objects.get_or_create(
        app_label=meta.app_label, model=meta.model_name
    )
    return tipo


def escanear(clases) -> list[dict]:
    encontrados: dict[str, dict] = {}

    for clase in clases:
        recurso_clase = getattr(clase, "_auto_permiso_clase", {}).get("recurso")

        for nombre, metodo in inspect.getmembers(clase, inspect.isfunction):
            if nombre.startswith("_") or nombre in _IGNORADOS:
                continue

            propia = getattr(metodo, METADATA, None)
            if propia is None and recurso_clase is None:
                continue

            datos = propia or {
                "recurso": recurso_clase,
                "operacion": nombre.lower(),
                "descripcion": "",
            }

            codename = codename_de(datos["recurso"], datos["operacion"])
            origen = getattr(metodo, "__qualname__", nombre)

            if codename in encontrados:
                # El MISMO método visto dos veces no es un duplicado: la
                # convención es `XxxMutations` + `XxxMutation` que hereda
                # de ella. Es la misma función.
                if encontrados[codename]["origen"] != origen:
                    encontrados[codename]["duplicado"] = True
                continue

            encontrados[codename] = {
                "codename": codename,
                "recurso": datos["recurso"],
                "operacion": datos["operacion"],
                "descripcion": datos["descripcion"],
                "metodo": f"{clase.__name__}.{nombre}",
                "origen": origen,
                "duplicado": False,
            }

    return sorted(encontrados.values(), key=lambda d: d["codename"])


__all__ = ["auto_permisos", "escanear", "codename_de", "content_type_del_ancla"]
