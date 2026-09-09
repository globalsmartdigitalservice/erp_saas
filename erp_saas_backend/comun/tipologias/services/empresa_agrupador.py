from django.core.exceptions import ValidationError

from comun.empresas import api as empresas
from comun.tipologias.constantes import AGRUPADOR
from comun.tipologias.models import EmpresaAgrupador
from comun.tipologias.repository import empresa_agrupador as repo


def _validar(empresa_id: int, agrupador: int) -> None:
    if agrupador not in AGRUPADOR.values:
        raise ValidationError(
            f"El agrupador {agrupador} no existe. Los declarados están en "
            f"comun/tipologias/constantes.py."
        )
    if empresas.obtener_empresa(empresa_id) is None:
        raise ValidationError(f"No existe la empresa {empresa_id}.")


def puede_ampliar(empresa_id: int, agrupador: int) -> bool:
    """
    ¿Esta empresa puede agregar valores propios a esa lista?

    EL PERMISO SE HEREDA DE LA MATRIZ, igual que los valores. Basta con
    que la fila esté cargada en la casa matriz para que sus sucursales
    puedan: es una capacidad que el proveedor le vende a un CLIENTE, y
    el cliente es el grupo entero. Cargar una fila por sucursal
    significaría que abrir una nueva la deja sin una función ya pagada.

    Lo que esto NO contesta es qué EMPLEADO puede apretar el botón: eso
    es un rol de usuario y vive en el módulo 12, todavía sin construir.
    En los ERP del mercado el reparto es el mismo —el alcance del dato
    lo da la estructura de empresas, el permiso lo da el rol—.
    """
    return repo.puede_ampliar(empresas.ids_del_ambito(empresa_id), agrupador)


def habilitar(empresa_id: int, agrupador: int) -> EmpresaAgrupador:
    _validar(empresa_id, agrupador)
    return repo.habilitar(empresa_id, agrupador)


def deshabilitar(empresa_id: int, agrupador: int) -> int:
    _validar(empresa_id, agrupador)
    return repo.deshabilitar(empresa_id, agrupador)


def listar_de_empresa(empresa_id: int) -> list[EmpresaAgrupador]:
    return repo.listar_de_empresa(empresa_id)
