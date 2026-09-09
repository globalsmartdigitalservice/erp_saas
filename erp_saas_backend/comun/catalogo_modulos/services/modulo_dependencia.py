from django.core.exceptions import ValidationError
from django.db import transaction

from comun.catalogo_modulos.models import ModuloDependencia
from comun.catalogo_modulos.repository import modulo_dependencia as repo
from comun.catalogo_modulos.repository import modulo_sistema as repo_modulo


def _modulo(modulo_id: int):
    fila = repo_modulo.obtener(modulo_id)
    if fila is None:
        raise ValidationError(f"No existe el módulo {modulo_id}.")
    return fila


def cadena_de(modulo_id: int) -> list[int]:
    """Todo lo que hace falta para que ese módulo funcione, no solo lo
    directo. Recorrido en anchura con memoria de visitados, así termina
    aunque hubiera un ciclo."""
    pendientes = [modulo_id]
    vistos: set[int] = set()
    cadena: list[int] = []

    while pendientes:
        actual = pendientes.pop(0)
        for requerido in repo.ids_requeridos_por(actual):
            if requerido in vistos:
                continue
            vistos.add(requerido)
            cadena.append(requerido)
            pendientes.append(requerido)

    return cadena


@transaction.atomic
def declarar(
    *, modulo_id: int, depende_de_id: int, tipo: str = ModuloDependencia.Tipo.DURA
) -> ModuloDependencia:
    _modulo(modulo_id)
    _modulo(depende_de_id)

    if modulo_id == depende_de_id:
        raise ValidationError("Un módulo no puede depender de sí mismo.")

    if repo.existe(modulo_id, depende_de_id):
        raise ValidationError("Esa dependencia ya está declarada.")

    if tipo not in ModuloDependencia.Tipo.values:
        raise ValidationError(
            f"'{tipo}' no es un tipo de dependencia. Es DURA (no funciona sin "
            f"él) o SUAVE (se integra si está)."
        )

    if modulo_id in cadena_de(depende_de_id):
        raise ValidationError(
            f"Esa dependencia formaría un ciclo: el módulo {depende_de_id} ya "
            f"necesita al {modulo_id}, directa o indirectamente. Una cadena "
            f"circular deja colgada la activación del módulo."
        )

    return repo.crear(
        modulo_id=modulo_id, depende_de_id=depende_de_id, tipo=tipo
    )


@transaction.atomic
def quitar(modulo_id: int, depende_de_id: int) -> None:
    """Se borra de verdad: una dependencia revocada no se archiva."""
    fila = repo.obtener(modulo_id, depende_de_id)
    if fila is None:
        raise ValidationError("Esa dependencia no está declarada.")

    repo.eliminar(fila)
