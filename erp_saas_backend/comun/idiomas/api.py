"""Superficie pública de `idiomas`. El resto de la app es privado.

    from comun.idiomas import api as idiomas

    disponibles = idiomas.listar_idiomas(solo_activos=True)

Cubre `Idioma` y `Traduccion`: los DATOS que carga cada empresa y el
usuario ve en un combo. `Recurso_Texto` —los textos de la interfaz— tiene
tabla pero no service: hoy los resuelve el frontend con sus propios
archivos, y la tabla espera al panel del proveedor que los edite sin
redesplegar.

Las lecturas van directo al repository; las escrituras pasan por services.
La excepción son las traducciones: elegir cuál gana —la propia, la de la
matriz o la de fábrica— es una decisión, y por eso va en el service.
"""

from comun.empresas import api as _empresas
from comun.idiomas import traducibles as _traducibles
from comun.idiomas.models import Idioma, Traduccion
from comun.idiomas.repository import idioma as _repo
from comun.idiomas.services import idioma as _svc
from comun.idiomas.services import traduccion as _svc_traduccion
from core.idioma import idioma_actual as _idioma_de_la_request
from core.tenancy import empresa_actual as _empresa_actual


def obtener_idioma(idioma_id: int) -> Idioma | None:
    return _repo.obtener(idioma_id)


def obtener_idiomas(idioma_ids) -> dict[int, Idioma]:
    return _repo.obtener_varios(idioma_ids)


def listar_idiomas(solo_activos: bool = False) -> list[Idioma]:
    """Todos los idiomas, o solo los activos."""
    return _repo.listar(solo_activos)


def obtener_por_codigo(codigo: str) -> Idioma | None:
    """Por su etiqueta (`es`, `es-bo`). La forma que usa Django."""
    return _repo.obtener_por_codigo((codigo or "").strip().lower())


def crear_idioma(*, codigo: str, nombre: str, activo: bool = True) -> Idioma:
    return _svc.crear(codigo=codigo, nombre=nombre, activo=activo)


def actualizar_idioma(idioma_id: int, **campos) -> Idioma:
    """No recibe `activo`: prender y apagar tienen sus propias funciones."""
    return _svc.actualizar(idioma_id, **campos)


def desactivar_idioma(idioma_id: int) -> Idioma:
    return _svc.desactivar(idioma_id)


def activar_idioma(idioma_id: int) -> Idioma:
    return _svc.activar(idioma_id)


def idioma_activo() -> int | None:
    """
    En qué idioma mostrar los textos. Se pregunta una vez por consulta,
    no una vez por fila.

    Busca el idioma de la request, después el `idioma_default` de la
    empresa activa, y si no hay ninguno devuelve None.

     **None NO es un error**: significa "mostrá los textos como están
    guardados", que es lo correcto para el panel del proveedor, los
    comandos y las semillas.
    """
    explicito = _idioma_de_la_request()
    if explicito is not None:
        return explicito

    empresa_id = _empresa_actual()
    if empresa_id is None:
        return None

    return _empresas.idioma_de(empresa_id)


def traducciones_de(
    entidad_tipo: str, entidad_ids, campo: str, idioma_id: int
) -> dict[int, str]:
    """
    Una consulta, N filas. Devuelve `{id: texto}` SOLO de las que tienen
    traducción; el fallback al original lo hace quien llama:

        textos = idiomas.traducciones_de(
            "conf_tipologia", [t.pk for t in filas], "nombre", idioma_id
        )
        for t in filas:
            nombre = textos.get(t.pk, t.nombre)     ← el original si no hay

    Va así porque el texto original vive en la tabla del otro módulo, que
    `idiomas` no puede leer sin cruzar una frontera de módulo.

     Nunca devuelve vacío para una fila sin traducción: la clave
    directamente no está. Un texto en blanco en un combo es peor que uno
    sin traducir.
    """
    return _svc_traduccion.textos_de(entidad_tipo, entidad_ids, campo, idioma_id)


def listar_traducciones_de(entidad_tipo: str, entidad_id: int) -> list[Traduccion]:
    """Todas las traducciones de UNA fila, en todos los idiomas y campos.

    Es lo que necesita el formulario de edición.
    """
    return _svc_traduccion.listar_de(entidad_tipo, entidad_id)


def guardar_traduccion(
    *, entidad_tipo: str, entidad_id: int, campo: str, idioma_id: int, texto: str
) -> Traduccion:
    """Crea o actualiza la traducción DE LA EMPRESA ACTIVA."""
    return _svc_traduccion.guardar(
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        campo=campo,
        idioma_id=idioma_id,
        texto=texto,
    )


def guardar_traduccion_de_fabrica(
    *, entidad_tipo: str, entidad_id: int, campo: str, idioma_id: int, texto: str
) -> Traduccion:
    """
    La del catálogo del sistema. Para las semillas y el panel del
    proveedor: hay que correrla dentro de `sin_filtro_de_empresa()`.
    """
    return _svc_traduccion.guardar_de_fabrica(
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        campo=campo,
        idioma_id=idioma_id,
        texto=texto,
    )


def borrar_traduccion(traduccion_id: int) -> None:
    """La fila vuelve a mostrarse en su idioma original."""
    _svc_traduccion.borrar(traduccion_id)


def tablas_traducibles() -> dict[str, tuple[str, ...]]:
    """Qué tablas se pueden traducir y qué campos de cada una.

    Lo consume el frontend para armar los formularios por idioma.
    """
    return dict(_traducibles.TRADUCIBLES)


__all__ = [
    "obtener_idioma",
    "obtener_idiomas",
    "listar_idiomas",
    "obtener_por_codigo",
    "crear_idioma",
    "actualizar_idioma",
    "desactivar_idioma",
    "activar_idioma",
    "idioma_activo",
    "traducciones_de",
    "listar_traducciones_de",
    "guardar_traduccion",
    "guardar_traduccion_de_fabrica",
    "borrar_traduccion",
    "tablas_traducibles",
]
