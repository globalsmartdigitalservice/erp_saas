from django.db import transaction

from dominios.entidades.models import EncuestaSatisfaccion
from dominios.entidades.repository import encuesta_satisfaccion as repo
from dominios.entidades.services import _comun


@transaction.atomic
def registrar(
    *,
    entidad_id: int,
    fecha,
    puntaje: int,
    comentario: str = "",
) -> EncuestaSatisfaccion:
    """
    Se llama `registrar` y no `crear` a propósito: lo que entra es el
    registro de algo que pasó, no un dato que después se edita.
    """
    _comun.entidad(entidad_id)

    return repo.crear(
        entidad_id=entidad_id,
        fecha=fecha,
        puntaje=int(puntaje),
        comentario=comentario,
    )
