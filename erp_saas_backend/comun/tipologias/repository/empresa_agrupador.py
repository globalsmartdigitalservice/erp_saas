"""Acceso a datos de `EmpresaAgrupador`."""

from comun.tipologias.models import EmpresaAgrupador


def puede_ampliar(empresa_ids, agrupador: int) -> bool:
    """
    Una consulta, sin JOIN, contra el índice único (empresa, agrupador).

    Recibe una LISTA de empresas —el ámbito: la propia y su matriz—
    porque el permiso se hereda. Quién arma esa lista es el service: el
    repository no sabe de jerarquías.

    Se llama solo al AGREGAR un valor —una vez cada tanto—, nunca al
    listar un combo. Ésa es toda la idea del diseño.
    """
    return EmpresaAgrupador.objects.filter(
        empresa_id__in=empresa_ids, agrupador=agrupador
    ).exists()


def listar_de_empresa(empresa_id: int) -> list[EmpresaAgrupador]:
    """
    Las listas habilitadas de una empresa. Para el panel del proveedor.

    El NOMBRE de cada lista no sale de acá: se resuelve aparte, por
    lote, contra las cabeceras (`tipologia` con `indice = 0`).
    """
    return list(EmpresaAgrupador.objects.filter(empresa_id=empresa_id))


def habilitar(empresa_id: int, agrupador: int) -> EmpresaAgrupador:
    """Idempotente: habilitar dos veces deja una sola fila."""
    fila, _ = EmpresaAgrupador.objects.get_or_create(
        empresa_id=empresa_id, agrupador=agrupador
    )
    return fila


def deshabilitar(empresa_id: int, agrupador: int) -> int:
    """
    Borra la fila. Acá SÍ se borra de verdad, y es la excepción a la
    regla del soft delete del ERP: esto no es un dato del negocio, es un
    permiso. Un permiso revocado no se archiva, se saca — y su ausencia
    ya significa "no puede".
    """
    borradas, _ = EmpresaAgrupador.objects.filter(
        empresa_id=empresa_id, agrupador=agrupador
    ).delete()
    return borradas
