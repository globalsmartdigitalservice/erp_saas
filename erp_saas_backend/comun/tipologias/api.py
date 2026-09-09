"""Superficie pública de `tipologias`. El resto de la app es privado.

    from comun.tipologias import api as tipologias
    from comun.tipologias.constantes import AGRUPADOR

    rubros = tipologias.de(AGRUPADOR.RUBRO)

 La versión por lote no es opcional acá: a esta app la referencian 154
tablas, y sin ella cada listado que muestre un estado dispara una consulta
por fila.

Las lecturas van al repository; las escrituras pasan por services, que es
donde están los invariantes del aislamiento.
"""

from django.core.exceptions import ValidationError

from comun.tipologias.constantes import AGRUPADOR, INDICE_CABECERA
from comun.tipologias.models import Tipologia
from core.tenancy import empresa_actual
from comun.tipologias.repository import tipologia as _repo
from comun.tipologias.services import empresa_agrupador as _svc_permiso
from comun.tipologias.services import tipologia as _svc
from comun.tipologias.services import tipologia_oculta as _svc_oculta


def de(agrupador: int, solo_activas: bool = True) -> list[Tipologia]:
    """
    Las tipologías de una lista tal como las ve la empresa activa: las
    suyas, las heredadas de su casa matriz y las de fábrica, menos las
    que ella tenga ocultas. Es la forma OBLIGATORIA de consultarlas
    — nunca `filter(agrupador=3)` a mano.
    """
    return _repo.listar_del_agrupador(agrupador, solo_activas)


def obtener(tipologia_id: int) -> Tipologia | None:
    return _repo.obtener(tipologia_id)


def obtener_varias(ids) -> dict[int, Tipologia]:
    return _repo.obtener_varias(ids)


class TipologiaEquivocada(ValidationError):
    """Se mandó una tipología que no sirve para ese campo."""


def exigir_del_agrupador(
    tipologia_id: int, agrupador: int, para: str
) -> "Tipologia":
    """
    Valida la tipología y levanta con el motivo real. Devuelve la fila.

        tipologias.exigir_del_agrupador(
            estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado de membresía"
        )

    `para` es cómo se llama ese campo en la frase del error.

    Distingue tres casos —no existe, es la CABECERA de la lista, es de
    otra lista— porque un único mensaje mentía en el más frecuente: la
    cabecera SÍ pertenece al agrupador, pero no es un valor de la lista.

     No delata tipologías de otra empresa: el manager no las devuelve,
    así que caen en la rama de "no existe" sin decir su nombre.
    """
    # Se mira INCLUYENDO cabeceras: si no, mandar el id de una sería
    # indistinguible de mandar un id inexistente, y el error diría "no
    # existe" para una fila que existe. El aislamiento no cambia — sigue
    # yendo por el manager multiempresa.
    fila = _repo.obtener_incluso_cabecera(tipologia_id)

    if fila is None:
        raise TipologiaEquivocada(
            f"No existe la tipología {tipologia_id}, o no está disponible "
            f"para esta empresa. Se esperaba un {para}."
        )

    if fila.indice == INDICE_CABECERA:
        raise TipologiaEquivocada(
            f"La tipología {tipologia_id} es el NOMBRE de la lista "
            f"'{fila.nombre}', no uno de sus valores. Seleccione un valor de esa "
            f"lista para el {para}."
        )

    if fila.agrupador != agrupador:
        raise TipologiaEquivocada(
            f"La tipología {tipologia_id} es '{fila.nombre}', de otra lista. "
            f"Se esperaba un {para}."
        )

    return fila


def es_del_agrupador(tipologia_id: int, agrupador: int) -> bool:
    """
    ¿Esa tipología pertenece a esa lista?

     Es LA validación que la base no puede hacer: todas las FK apuntan a
    `tipologia` entera, así que nada impide poner el id de "S.R.L." en el
    campo `estado` de un país. Postgres lo acepta y el catálogo queda
    mezclado en silencio. Una CABECERA tampoco pasa.
    """
    return (
        Tipologia.objects.valores()
        .filter(pk=tipologia_id, agrupador=agrupador)
        .exists()
    )


def obtener_del_sistema(agrupador: int, nombre: str) -> Tipologia | None:
    """
    Una fila del CATÁLOGO DEL SISTEMA por su nombre — la que garantiza la
    semilla, como la "BAJA" del soft delete. Dice `del_sistema` y no
    `por_nombre` a propósito: se quiere la global, no una que una empresa
    se haya creado con el mismo nombre.
    """
    return _repo.obtener_del_sistema(agrupador, nombre)


def agrupadores() -> list[Tipologia]:
    """
    Las listas del sistema con su nombre: las CABECERAS.

     Devuelve vacío si no se corrió `cargar_semillas`, que es el motivo
    por el que la semilla dejó de ser opcional en el arranque.
    """
    return _repo.listar_cabeceras()


def nombre_de_la_lista(agrupador: int) -> str | None:
    """El nombre de UNA lista. None si le falta la cabecera."""
    cabecera = _repo.obtener_cabecera(agrupador)
    return cabecera.nombre if cabecera else None


def puede_ampliar(agrupador: int) -> bool:
    """
    ¿La empresa ACTIVA puede agregar valores a esa lista?

    Para que la pantalla no ofrezca el botón "Agregar" si no va. El
    rechazo de verdad lo hace `crear()`; esto es solo para la interfaz.
    """
    empresa_id = empresa_actual()
    return empresa_id is not None and _svc_permiso.puede_ampliar(
        empresa_id, agrupador
    )


def agrupadores_ampliables_de(empresa_id: int) -> list[int]:
    """Las listas habilitadas de una empresa. Para el panel del proveedor."""
    return [f.agrupador for f in _svc_permiso.listar_de_empresa(empresa_id)]


def habilitar_agrupador(empresa_id: int, agrupador: int):
    """
    Habilita una lista para un cliente. **Del panel del proveedor**, no
    del cliente. Idempotente.
    """
    return _svc_permiso.habilitar(empresa_id, agrupador)


def deshabilitar_agrupador(empresa_id: int, agrupador: int) -> int:
    """Revoca el permiso. Borra la fila: un permiso revocado no se archiva."""
    return _svc_permiso.deshabilitar(empresa_id, agrupador)


def ocultar(tipologia_id: int):
    """
    La empresa activa deja de ver ese valor. **Nadie más se entera.**

    No confundir con `desactivar`:

        desactivar  →  el valor muere para TODO el grupo  ·  solo lo propio
        ocultar     →  deja de verlo SOLO esta empresa    ·  cualquier valor visible

    Es lo único que tiene una sucursal para sacarse de la pantalla algo de
    fábrica o de su matriz. Idempotente.
    """
    return _svc_oculta.ocultar(tipologia_id)


def mostrar(tipologia_id: int) -> int:
    """Deshace un ocultamiento. Devuelve cuántas filas borró (0 o 1)."""
    return _svc_oculta.mostrar(tipologia_id)


def esta_oculta(tipologia_id: int) -> bool:
    return _svc_oculta.esta_oculta(tipologia_id)


def listar_ocultas(agrupador: int | None = None) -> list[Tipologia]:
    """
    Lo que la empresa activa escondió. Existe aparte porque `de()`
    justamente NO las devuelve, y sin esto no habría cómo volver a
    mostrarlas.
    """
    return _svc_oculta.listar_ocultas(agrupador)


def crear(
    *, agrupador: int, nombre: str, abreviatura: str = "", indice: int | None = None
) -> Tipologia:
    """
    No recibe `empresa_id` y nunca lo va a recibir: sale del contexto.

    Sin `indice`, el valor va al final de la lista. El 0 se rechaza: es
    la cabecera.
    """
    return _svc.crear(
        agrupador=agrupador, nombre=nombre, abreviatura=abreviatura, indice=indice
    )


def actualizar(tipologia_id: int, **campos) -> Tipologia:
    return _svc.actualizar(tipologia_id, **campos)


def desactivar(tipologia_id: int) -> Tipologia:
    """
    Soft delete de una tipología PROPIA. Muere para todo el grupo.

    Una fila heredada de la matriz o de fábrica se rechaza: lo que
    corresponde ahí es `ocultar`.
    """
    return _svc.desactivar(tipologia_id)


__all__ = [
    "de",
    "obtener",
    "obtener_varias",
    "es_del_agrupador",
    "exigir_del_agrupador",
    "TipologiaEquivocada",
    "obtener_del_sistema",
    "agrupadores",
    "nombre_de_la_lista",
    "puede_ampliar",
    "agrupadores_ampliables_de",
    "habilitar_agrupador",
    "deshabilitar_agrupador",
    "ocultar",
    "mostrar",
    "esta_oculta",
    "listar_ocultas",
    "crear",
    "actualizar",
    "desactivar",
    "AGRUPADOR",
    "INDICE_CABECERA",
]
