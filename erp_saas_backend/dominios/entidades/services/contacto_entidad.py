from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias.constantes import AGRUPADOR
from dominios.entidades.models import ContactoEntidad
from dominios.entidades.repository import contacto_entidad as repo
from dominios.entidades.services import _comun


@transaction.atomic
def crear(
    *,
    entidad_id: int,
    nombre: str,
    estado_id: int,
    cargo: str = "",
    email: str = "",
    telefono: str = "",
) -> ContactoEntidad:
    _comun.entidad(entidad_id)
    _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)

    return repo.crear(
        entidad_id=entidad_id,
        nombre=nombre,
        cargo=cargo,
        email=email,
        telefono=telefono,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    contacto_id: int,
    *,
    nombre: str | None = None,
    cargo: str | None = None,
    email: str | None = None,
    telefono: str | None = None,
    estado_id: int | None = None,
) -> ContactoEntidad:
    fila = repo.obtener(contacto_id)
    if fila is None:
        raise ValidationError(f"No existe el contacto {contacto_id}.")

    if estado_id is not None:
        _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)

    campos = _comun.solo_los_dados(
        nombre=nombre,
        cargo=cargo,
        email=email,
        telefono=telefono,
        estado_id=estado_id,
    )
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(contacto_id: int) -> ContactoEntidad:
    fila = repo.obtener(contacto_id)
    if fila is None:
        raise ValidationError(f"No existe el contacto {contacto_id}.")

    return repo.actualizar(fila, estado_id=_comun.estado_de_baja().pk)
