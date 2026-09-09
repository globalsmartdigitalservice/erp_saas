from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias.models import Tipologia, TipologiaOculta
from comun.tipologias.repository import tipologia as repo_tipologia
from comun.tipologias.repository import tipologia_oculta as repo
from core.tenancy import empresa_actual


def _empresa_del_contexto() -> int:
    empresa_id = empresa_actual()
    if empresa_id is None:
        raise ValidationError(
            "No hay empresa en el contexto. Ocultar un valor es una decisión "
            "DE UNA empresa: sin saber cuál, no se puede."
        )
    return empresa_id


@transaction.atomic
def ocultar(tipologia_id: int) -> TipologiaOculta:
    """
    La empresa activa deja de ver ese valor. Nadie más se entera.
    Idempotente.

     El orden de los dos pasos NO es intercambiable: una vez oculta, la
    fila deja de ser visible para esta empresa, así que preguntarle al
    manager si existe la daría por inexistente y la segunda llamada
    fallaría con "no existe". Por eso "¿ya está oculta?" va PRIMERO.
    """
    empresa_id = _empresa_del_contexto()

    if not repo.esta_oculta(empresa_id, tipologia_id):
        # Solo acá tiene sentido preguntar por el manager: una fila de
        # otro cliente da None y termina.
        if repo_tipologia.obtener(tipologia_id) is None:
            raise ValidationError(f"No existe la tipología {tipologia_id}.")

    return repo.ocultar(empresa_id, tipologia_id)


@transaction.atomic
def mostrar(tipologia_id: int) -> int:
    """
    Deshace un ocultamiento.

     Acá NO se valida contra el manager: la fila está oculta justamente
    para esta empresa, así que no la devuelve, y validando no se podría
    volver a mostrar ningún valor oculto nunca.
    """
    empresa_id = _empresa_del_contexto()
    return repo.mostrar(empresa_id, tipologia_id)


def esta_oculta(tipologia_id: int) -> bool:
    empresa_id = empresa_actual()
    return empresa_id is not None and repo.esta_oculta(empresa_id, tipologia_id)


def listar_ocultas(agrupador: int | None = None) -> list[Tipologia]:
    """Las que esta empresa escondió. Para la pantalla de configuración."""
    empresa_id = empresa_actual()
    if empresa_id is None:
        return []
    return repo.listar_tipologias_ocultas(empresa_id, agrupador)
