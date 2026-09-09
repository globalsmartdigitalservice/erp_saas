from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias.constantes import AGRUPADOR, INDICE_CABECERA
from comun.tipologias.models import Tipologia
from comun.tipologias.repository import tipologia as repo
from comun.tipologias.services import empresa_agrupador as svc_permiso
from core.tenancy import empresa_actual


def _validar_agrupador(agrupador: int) -> None:
    """
    INVARIANTE 1 — el agrupador tiene que estar declarado.

    `agrupador` es un `IntegerField` libre: sin esto, un 999 crea una
    lista fantasma que ninguna pantalla muestra y que nadie encuentra
    después.
    """
    if agrupador not in AGRUPADOR.values:
        raise ValidationError(
            f"El agrupador {agrupador} no existe. Los declarados están en "
            f"comun/tipologias/constantes.py."
        )


def _empresa_del_contexto() -> int:
    """
    INVARIANTE 2 — la empresa sale del contexto, nunca del input.

    Si no hay empresa activa se rechaza en vez de crear una fila del
    sistema por accidente. Esa fila la vería todo el mundo.
    """
    empresa_id = empresa_actual()
    if empresa_id is None:
        raise ValidationError(
            "No hay empresa en el contexto. Una tipología de empresa no se "
            "puede crear sin saber de quién es; las del sistema se cargan "
            "con `cargar_semillas` o desde el panel del proveedor."
        )
    return empresa_id


def _exigir_que_sea_propia(tipologia: Tipologia) -> None:
    """
    INVARIANTE 3 — solo se escribe sobre la fila PROPIA.

    Es el agujero 2. El manager muestra tres cosas y solo una es
    modificable:

        empresa = NULL        →  de fábrica   →  la comparten todos los clientes
        empresa = la matriz   →  heredada     →  la comparten las hermanas
        empresa = la activa   →  propia       →  ÉSTA, y solo ésta

    Los dos mensajes son distintos a propósito: el de la matriz manda a
    ocultar, que es lo que la sucursal sí puede hacer.
    """
    if tipologia.empresa_id is None:
        raise ValidationError(
            f"'{tipologia.nombre}' es del catálogo del sistema y lo comparten "
            f"todas las empresas: no se puede modificar ni desactivar desde acá."
        )
    if tipologia.empresa_id != empresa_actual():
        raise ValidationError(
            f"'{tipologia.nombre}' es de la casa matriz y lo comparten todas "
            f"sus sucursales: no se puede modificar ni desactivar desde acá. "
            f"Si esta empresa no lo usa, puede ocultarlo."
        )


def _validar_nombre_libre(
    agrupador: int, nombre: str, excluir_id: int | None = None
) -> None:
    """
    INVARIANTE 4 — el nombre no se repite EN LO QUE LA EMPRESA VE.

    Es más ancho que la constraint de la base, y tiene que serlo: es el
    agujero 4. La constraint solo mira (empresa, agrupador, nombre), así
    que no ve venir el "QR" de la sucursal contra el "QR" heredado de la
    matriz —son filas de empresas distintas— y el combo termina con dos.
    """
    if repo.existe_nombre_visible(agrupador, nombre, excluir_id):
        raise ValidationError(
            f"Ya existe '{nombre}' en esa lista. Dos valores con el mismo "
            f"nombre dejan a cualquiera sin saber cuál usar."
        )


def _validar_permiso_de_ampliar(empresa_id: int, agrupador: int) -> None:
    """
    INVARIANTE 5 — no toda lista es ampliable por el cliente.

    Los rubros los define solo el proveedor; las formas de pago tocan
    contabilidad; los estados los lee el código. Pero cuáles se
    habilitan **no se decide en el código**: es un dato de
    `empresa_agrupador`, que el proveedor carga por cliente sin
    redesplegar.

    El permiso se HEREDA de la matriz, igual que los valores: es una
    capacidad que el proveedor le vende a un CLIENTE, y el cliente es el
    grupo entero —si abre una sucursal el lunes no puede quedarse sin la
    función que ya pagó—. Qué EMPLEADO puede apretar el botón es otra
    pregunta y se contesta con roles, en el módulo 12.

    SIN FILA = SIN PERMISO. La tabla arranca vacía, así que hoy nadie
    puede ampliar nada — que es exactamente lo definido mientras se
    analiza lista por lista cuáles habilitar. Falla cerrado: un olvido
    deja a un cliente sin poder agregar (molesta), nunca agregando donde
    no debe (caro).

    """
    if not svc_permiso.puede_ampliar(empresa_id, agrupador):
        raise ValidationError(
            f"Esta empresa no puede agregar valores propios a esa lista. "
            f"Si corresponde, el proveedor tiene que habilitarla."
        )


def _validar_indice(indice: int) -> None:
    """
    INVARIANTE 6 — el índice 0 está reservado para la cabecera.

    `indice = 0` es la fila que guarda el NOMBRE de la lista, y
    ninguna consulta de valores la devuelve. Si un valor naciera con 0,
    desaparecería de todos los combos sin dar error: el cliente lo
    crearía, el sistema le diría que sí, y no lo vería nunca más.

    Es un caso realista, no teórico: 0 es el default de la columna.
    """
    if indice <= INDICE_CABECERA:
        raise ValidationError(
            f"El índice {indice} no se puede usar: el 0 está reservado para el "
            f"nombre de la lista. Los valores van de 1 en adelante."
        )


def _obtener_o_fallar(tipologia_id: int) -> Tipologia:
    tipologia = repo.obtener(tipologia_id)
    if tipologia is None:
        # También cae acá una tipología de OTRA empresa: el manager no
        # la devuelve. El mensaje no distingue los dos casos a
        # propósito — decir "existe pero no es tuya" ya filtra
        # información de otro cliente.
        raise ValidationError(f"No existe la tipología {tipologia_id}.")
    return tipologia


@transaction.atomic
def crear(
    *, agrupador: int, nombre: str, abreviatura: str = "", indice: int | None = None
) -> Tipologia:
    """
    Crea una tipología DE LA EMPRESA ACTIVA.

    No hay parámetro `empresa_id` y no lo va a haber: si el cliente
    pudiera mandarlo, podría crear filas para otra empresa o para el
    sistema (mass assignment).

    `indice` sí se puede mandar —es el orden en el combo, una decisión
    del que carga—, pero si no viene lo calcula el sistema: va al final
    de la lista. Antes el default era 0, que ahora es la cabecera.
    """
    _validar_agrupador(agrupador)
    empresa_id = _empresa_del_contexto()
    _validar_permiso_de_ampliar(empresa_id, agrupador)
    _validar_nombre_libre(agrupador, nombre)

    if indice is None:
        indice = repo.siguiente_indice(agrupador)
    _validar_indice(indice)

    return repo.crear(
        empresa_id=empresa_id,
        agrupador=agrupador,
        nombre=nombre,
        abreviatura=abreviatura,
        indice=indice,
    )


@transaction.atomic
def actualizar(
    tipologia_id: int,
    *,
    nombre: str | None = None,
    abreviatura: str | None = None,
    indice: int | None = None,
) -> Tipologia:
    """
    Cambia los datos de una tipología propia.

    El `agrupador` NO se puede cambiar: mover un valor de una lista a
    otra deja huérfanas a todas las filas que ya lo apuntaban. Si hace
    falta, se desactiva y se crea uno nuevo.
    """
    tipologia = _obtener_o_fallar(tipologia_id)
    _exigir_que_sea_propia(tipologia)

    if nombre is not None:
        _validar_nombre_libre(tipologia.agrupador, nombre, excluir_id=tipologia_id)

    if indice is not None:
        _validar_indice(indice)

    campos = {
        campo: valor
        for campo, valor in (
            ("nombre", nombre),
            ("abreviatura", abreviatura),
            ("indice", indice),
        )
        if valor is not None
    }
    if not campos:
        return tipologia

    return repo.actualizar(tipologia, **campos)


@transaction.atomic
def desactivar(tipologia_id: int) -> Tipologia:
    """
    Soft delete.

    Acá el estado NO es una FK a Tipologia —se apuntaría a sí misma—
    sino un entero con choices. Es la excepción del sistema.

     Desactivar MATA el valor para todo el grupo: la fila es una sola,
    así que las sucursales dejan de verlo también. Si lo que se quiere es
    dejar de verlo SOLO acá, eso es `ocultar()`, no esto.

    Se permite desactivar una tipología que otras filas estén usando: la
    fila no se va, así que las FK existentes siguen funcionando; solo
    deja de ofrecerse en los combos. Prohibirlo obligaría a revisar 154
    tablas en cada baja.
    """
    tipologia = _obtener_o_fallar(tipologia_id)
    _exigir_que_sea_propia(tipologia)

    return repo.actualizar(tipologia, estado=Tipologia.Estado.INACTIVO)
