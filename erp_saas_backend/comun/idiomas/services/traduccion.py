from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction

from comun.idiomas import traducibles
from comun.idiomas.models import Traduccion
from comun.idiomas.repository import idioma as repo_idioma
from comun.idiomas.repository import traduccion as repo
from core.tenancy import empresa_actual, filtro_desactivado

# Cache de db_table → modelo. Se arma una vez: el registro de apps de
# Django no cambia después del arranque.
_MODELOS_POR_TABLA: dict[str, type] | None = None


def _modelo_de(entidad_tipo: str):
    global _MODELOS_POR_TABLA

    if _MODELOS_POR_TABLA is None:
        _MODELOS_POR_TABLA = {m._meta.db_table: m for m in apps.get_models()}

    return _MODELOS_POR_TABLA.get(entidad_tipo)


def _validar_traducible(entidad_tipo: str, campo: str) -> None:
    """
    La defensa contra la falla silenciosa.

    Con texto libre, `"conf_tipologa"` se guardaría igual y esa fila no
    traduciría nunca sin dar ningún error. Ver `traducibles.py`.
    """
    if not traducibles.es_traducible(entidad_tipo):
        raise ValidationError(
            f"La tabla '{entidad_tipo}' no está declarada como traducible. "
            f"Las que sí lo están: {', '.join(traducibles.tablas())}."
        )

    campos = traducibles.campos_de(entidad_tipo)
    if campo not in campos:
        raise ValidationError(
            f"El campo '{campo}' de '{entidad_tipo}' no es traducible. "
            f"Los de esa tabla son: {', '.join(campos)}."
        )


def _validar_texto(texto: str) -> str:
    """
    Una traducción vacía no es una traducción: es la ausencia de una.

    Se rechaza en vez de guardarla, porque una fila con texto vacío haría
    que el combo mostrara un renglón en blanco en lugar de caer al texto
    original. Para sacar una traducción está `borrar()`.
    """
    limpio = (texto or "").strip()
    if not limpio:
        raise ValidationError(
            "La traducción no puede estar vacía. Si querés sacarla, borrala."
        )
    return limpio


def _validar_idioma(idioma_id: int):
    idioma = repo_idioma.obtener(idioma_id)
    if idioma is None:
        raise ValidationError(f"No existe el idioma {idioma_id}.")

    if not idioma.activo:
        raise ValidationError(
            f"'{idioma.nombre}' está desactivado: no se puede cargar "
            f"traducciones en un idioma que no se ofrece."
        )
    return idioma


def _empresa_del_contexto() -> int:
    empresa_id = empresa_actual()
    if empresa_id is None:
        raise ValidationError(
            "No hay empresa activa: no se sabe de quién sería esta "
            "traducción. Para cargar las del catálogo del sistema está "
            "guardar_de_fabrica()."
        )
    return empresa_id


def _validar_fila_visible(entidad_tipo: str, entidad_id: int) -> None:
    """
    Aislamiento: la fila traducida se resuelve contra el queryset YA FILTRADO.

    `_default_manager` es el manager de esa tabla —tenant en casi todas—,
    así que una fila de otra empresa "no existe" y el mensaje no delata
    que el id exista en otro lado.

    De paso agarra el id inventado, que es la misma falla silenciosa del
    nombre de tabla: se guardaría una fila que no traduce nada.
    """
    modelo = _modelo_de(entidad_tipo)
    if modelo is None:
     
        raise ValidationError(
            f"'{entidad_tipo}' está en el registro de traducibles pero no "
            f"corresponde a ninguna tabla del proyecto."
        )

    if not modelo._default_manager.filter(pk=entidad_id).exists():
        raise ValidationError(
            f"No existe el registro {entidad_id} en '{entidad_tipo}'."
        )


def _exigir_que_sea_propia(traduccion: Traduccion) -> None:
    """
    Nadie borra lo que no es suyo.

    El manager deja VER las de fábrica y las de la casa matriz, así que
    sin esto una sucursal podría borrar la traducción que cargó su
    matriz y dejar sin traducir a las otras 19.
    """
    empresa_id = empresa_actual()

    if traduccion.empresa_id is None:
        raise ValidationError(
            "Esa traducción es del catálogo del sistema y no se toca desde "
            "una empresa. Si necesitás otro texto, guardá el tuyo: el propio "
            "le gana al de fábrica."
        )

    if traduccion.empresa_id != empresa_id:
        raise ValidationError(
            "Esa traducción es de tu casa matriz. Si necesitás otro texto, "
            "guardá el tuyo: el propio le gana al heredado."
        )


def _rango(fila: Traduccion, empresa_id: int | None) -> int:
    """
    Cuál gana cuando hay varias para la misma fila:

        2  la propia
        1  la de la casa matriz (el manager ya descartó las ajenas)
        0  la de fábrica
    """
    if fila.empresa_id is None:
        return 0
    if fila.empresa_id == empresa_id:
        return 2
    return 1


def textos_de(
    entidad_tipo: str, entidad_ids, campo: str, idioma_id: int
) -> dict[int, str]:
    """
    Los textos traducidos de N filas, en UNA sola consulta.

     DEVUELVE SOLO LAS QUE TIENEN TRADUCCIÓN. El que llama hace el
    fallback con un `.get()`:

        textos = idiomas.traducciones_de("conf_tipologia", ids, "nombre", 2)
        nombre = textos.get(t.pk, t.nombre)      ← el original si no hay

    El fallback vive del lado del consumidor a propósito: el texto
    original está en la tabla del otro módulo y `idiomas` no la puede
    leer sin cruzar una frontera de módulo.
    """
    empresa_id = empresa_actual()

    elegidas: dict[int, tuple[int, str]] = {}
    for fila in repo.filas_para(entidad_tipo, entidad_ids, campo, idioma_id):
        rango = _rango(fila, empresa_id)
        actual = elegidas.get(fila.entidad_id)
        if actual is None or rango > actual[0]:
            elegidas[fila.entidad_id] = (rango, fila.texto)

    return {entidad_id: texto for entidad_id, (_, texto) in elegidas.items()}


def listar_de(entidad_tipo: str, entidad_id: int) -> list[Traduccion]:
    """Todas las traducciones de una fila. Lo consume el formulario."""
    return repo.listar_de(entidad_tipo, entidad_id)


@transaction.atomic
def guardar(
    *, entidad_tipo: str, entidad_id: int, campo: str, idioma_id: int, texto: str
) -> Traduccion:
    """
    Crea o actualiza LA TRADUCCIÓN DE LA EMPRESA ACTIVA.

    Es un upsert: si esa empresa ya tenía texto para ese campo y ese
    idioma, se pisa; si no, nace. Y nunca toca la de fábrica ni la de la
    matriz — ver el docstring del módulo.
    """
    _validar_traducible(entidad_tipo, campo)
    texto = _validar_texto(texto)
    _validar_idioma(idioma_id)
    empresa_id = _empresa_del_contexto()
    _validar_fila_visible(entidad_tipo, entidad_id)

    existente = repo.buscar(entidad_tipo, entidad_id, campo, idioma_id, empresa_id)
    if existente is not None:
        return repo.actualizar(existente, texto=texto)

    return repo.crear(
        empresa_id=empresa_id,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        campo=campo,
        idioma_id=idioma_id,
        texto=texto,
    )


@transaction.atomic
def guardar_de_fabrica(
    *, entidad_tipo: str, entidad_id: int, campo: str, idioma_id: int, texto: str
) -> Traduccion:
    """
    La traducción del CATÁLOGO DEL SISTEMA (`empresa = NULL`).

    La cargan las semillas y el panel del proveedor: "Comercio" es
    "Retail" para todos los clientes, no hay una versión por empresa.

    Exige correr dentro de `sin_filtro_de_empresa()`. No es una molestia
    burocrática: es lo que impide que una llamada suelta desde una
    pantalla del cliente escriba en el catálogo de todos. La intención de
    cruzar empresas queda escrita en el código que llama.
    """
    if not filtro_desactivado():
        raise ValidationError(
            "Las traducciones de fábrica se cargan con "
            "`sin_filtro_de_empresa()`: son del catálogo del sistema y las "
            "ve todo el mundo."
        )

    _validar_traducible(entidad_tipo, campo)
    texto = _validar_texto(texto)
    _validar_idioma(idioma_id)
    _validar_fila_visible(entidad_tipo, entidad_id)

    existente = repo.buscar(entidad_tipo, entidad_id, campo, idioma_id, None)
    if existente is not None:
        return repo.actualizar(existente, texto=texto)

    return repo.crear(
        empresa_id=None,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        campo=campo,
        idioma_id=idioma_id,
        texto=texto,
    )


@transaction.atomic
def borrar(traduccion_id: int) -> None:
    """
    Saca la traducción. La fila vuelve a mostrarse en su idioma original.

    Es idempotente en el sentido que importa: si ya no está, avisa que no
    existe en vez de fallar raro.
    """
    traduccion = repo.obtener(traduccion_id)
    if traduccion is None:
        raise ValidationError(f"No existe la traducción {traduccion_id}.")

    _exigir_que_sea_propia(traduccion)
    repo.borrar(traduccion)
