"""Las consultas de tipologías."""

import strawberry

from comun.idiomas import api as idiomas
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from comun.tipologias.models import Tipologia

from .types import AgrupadorType, TipologiaType

# El `db_table`, no un literal escrito a mano: es la misma cadena que
# guarda `Traduccion.entidad_tipo` y la que valida el registro de
# traducibles. Si algún día la tabla se renombra, esto la sigue solo.
TABLA = Tipologia._meta.db_table


def _codigo_de(agrupador: int) -> str:
    """
    El nombre de la constante: `5` → `"TIPO_ENTIDAD"`.

    Es la llave estable con la que el frontend pide cada lista, así que
    no puede salir de la base: sale del código, que es lo único que no
    cambia cuando se renumera o se renombra una cabecera.

    Devuelve `""` si la cabecera apunta a un agrupador que no está
    declarado. No debería pasar —`crear()` valida el agrupador—, pero
    reventar acá dejaría toda la pantalla de configuración sin cargar
    por una fila suelta mal sembrada.
    """
    try:
        return AGRUPADOR(agrupador).name
    except ValueError:
        return ""


def _traducidas(filas) -> list[TipologiaType]:
    """
    Arma los tipos con los textos en el idioma activo.

    Son DOS consultas fijas —una por campo traducible—, no dos por fila.
    Se podrían colapsar en una sola pidiendo los dos campos juntos; no
    se hizo porque complicaría la firma de `traducciones_de()` para las
    30 apps que vienen, y dos consultas constantes no se notan. Si algún
    día se mide que molestan, el cambio es adentro de esta función.
    """
    if not filas:
        return []

    idioma_id = idiomas.idioma_activo()

    # Sin idioma activo no se consulta nada: cada texto sale como está
    # guardado. Es el caso del panel del proveedor y de los comandos.
    if idioma_id is None:
        return [TipologiaType.desde_modelo(t) for t in filas]

    ids = [t.pk for t in filas]
    nombres = idiomas.traducciones_de(TABLA, ids, "nombre", idioma_id)
    abreviaturas = idiomas.traducciones_de(TABLA, ids, "abreviatura", idioma_id)

    # `.get()` sin default: lo que no tiene traducción llega como None y
    # el type cae solo al texto original.
    return [
        TipologiaType.desde_modelo(
            t, nombre=nombres.get(t.pk), abreviatura=abreviaturas.get(t.pk)
        )
        for t in filas
    ]


@strawberry.type
class TipologiaQueries:
    @strawberry.field(
        description="Los valores de una lista tal como los ve la empresa "
        "activa: los suyos, los heredados de su casa matriz y los de fábrica, "
        "menos los que ella tenga ocultos. Alimenta todos los combos del ERP. "
        "Los textos vienen en el idioma activo; el que no esté traducido sale "
        "como fue cargado."
    )
    def tipologias(self, agrupador: int, solo_activas: bool = True) -> list[TipologiaType]:
        return _traducidas(tipologias.de(agrupador, solo_activas))

    @strawberry.field(
        description="Los valores que la empresa activa tiene OCULTOS. No "
        "salen en `tipologias` —justamente por estar ocultos—, así que la "
        "pantalla de configuración los pide por acá para poder mostrarlos "
        "de nuevo."
    )
    def tipologias_ocultas(self, agrupador: int | None = None) -> list[TipologiaType]:
        return _traducidas(tipologias.listar_ocultas(agrupador))

    @strawberry.field(description="Una tipología por su id.")
    def tipologia(self, id: strawberry.ID) -> TipologiaType | None:
        fila = tipologias.obtener(int(id))
        if fila is None:
            return None
        return _traducidas([fila])[0]

    @strawberry.field(
        description="Las listas del sistema con su nombre, para que el "
        "frontend no hardcodee los números ni los títulos. El nombre sale de "
        "la cabecera de cada lista, así que el proveedor lo puede cambiar sin "
        "redesplegar. Vacío si no se cargaron las semillas."
    )
    def agrupadores(self) -> list[AgrupadorType]:
        # Las cabeceras también son filas de `conf_tipologia`, así que su
        # nombre se traduce igual: el título "Rubros" tiene que salir
        # "Industries" en la misma pantalla donde salen sus valores.
        #
        # Y por eso mismo el `codigo` NO se traduce ni se toca: es la
        # llave con la que el frontend pide cada lista. Si viajara
        # traducido, el combo funcionaría en español y quedaría vacío en
        # inglés. Ver el docstring de `AgrupadorType`.
        return [
            AgrupadorType(
                valor=fila.agrupador,
                nombre=fila.nombre,
                codigo=_codigo_de(fila.agrupador),
            )
            for fila in _traducidas(tipologias.agrupadores())
        ]


@strawberry.type
class TipologiaQuery(TipologiaQueries):
    """La superficie de consulta de tipologías. Solo compone."""
