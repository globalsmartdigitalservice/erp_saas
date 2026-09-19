from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas.models import EmpresaMoneda
from comun.empresas.repository import empresa as repo_empresa
from comun.empresas.repository import empresa_moneda as repo
from comun.monedas import api as monedas
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO


def _validar_empresa(empresa_id: int) -> None:
    if repo_empresa.obtener(empresa_id) is None:
        raise ValidationError(f"No existe la empresa {empresa_id}.")


def _validar_moneda(moneda_id: int):
    moneda = monedas.obtener_moneda(moneda_id)
    if moneda is None:
        raise ValidationError(f"No existe la moneda {moneda_id}.")
    return moneda


def _estado_activo():
    fila = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
    )
    if fila is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_ACTIVO}' del agrupador "
            f"ESTADO_REGISTRO. Ejecute: python manage.py cargar_semillas"
        )
    return fila


@transaction.atomic
def agregar(
    *, empresa_id: int, moneda_id: int, es_moneda_oficial: bool = False
) -> EmpresaMoneda:
    """La primera moneda que se agrega tiene que ser la oficial —sin base de
    conversión no hay `montoBase`—, así que se marca sola."""
    _validar_empresa(empresa_id)
    moneda = _validar_moneda(moneda_id)

    if repo.existe(empresa_id, moneda_id):
        raise ValidationError(
            f"Esa empresa ya opera con {moneda.codigo}. Si desea que sea su "
            f"moneda oficial, márquela; no es necesario agregarla de nuevo."
        )

    # INVARIANTE 4, primera mitad: si es la primera, es la oficial.
    if repo.obtener_oficial_de(empresa_id) is None:
        es_moneda_oficial = True
    elif es_moneda_oficial:
        # Marcar una nueva desmarca la anterior, acá adentro.
        repo.desmarcar_oficiales(empresa_id)

    return repo.crear(
        empresa_id=empresa_id,
        moneda_id=moneda_id,
        es_moneda_oficial=es_moneda_oficial,
        estado_id=_estado_activo().pk,
    )


@transaction.atomic
def marcar_oficial(empresa_id: int, moneda_id: int) -> EmpresaMoneda:
    """Cambia la moneda base. No reescribe historia: los documentos ya
    emitidos guardan el `montoBase` de su momento."""
    _validar_empresa(empresa_id)
    moneda = _validar_moneda(moneda_id)

    fila = None
    for f in repo.listar_de(empresa_id):
        if f.moneda_id == moneda_id:
            fila = f
            break

    if fila is None:
        raise ValidationError(
            f"Esa empresa no opera con {moneda.codigo}. Agregala primero."
        )

    if fila.es_moneda_oficial:
        return fila

    repo.desmarcar_oficiales(empresa_id, excluir_id=fila.pk)
    return repo.actualizar(fila, es_moneda_oficial=True)


@transaction.atomic
def quitar(empresa_id: int, moneda_id: int) -> int:
    """Soft delete. La oficial no se puede quitar: la empresa quedaría sin
    base de conversión."""
    _validar_empresa(empresa_id)
    moneda = _validar_moneda(moneda_id)

    fila = None
    for f in repo.listar_de(empresa_id):
        if f.moneda_id == moneda_id:
            fila = f
            break

    if fila is None:
        raise ValidationError(f"Esa empresa no opera con {moneda.codigo}.")

    if fila.es_moneda_oficial:
        raise ValidationError(
            f"'{moneda.codigo}' es la moneda oficial de esa empresa y no se "
            f"puede quitar. Marque otra como oficial primero."
        )

    from comun.tipologias.constantes import NOMBRE_ESTADO_BAJA

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Ejecute: python manage.py cargar_semillas"
        )

    repo.actualizar(fila, estado=baja)
    return 1


def moneda_oficial_de(empresa_id: int):
    fila = repo.obtener_oficial_de(empresa_id)
    return monedas.obtener_moneda(fila.moneda_id) if fila else None


def listar_de(empresa_id: int) -> list[EmpresaMoneda]:
    return repo.listar_de(empresa_id)
