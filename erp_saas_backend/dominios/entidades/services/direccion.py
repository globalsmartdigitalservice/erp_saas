from django.core.exceptions import ValidationError
from django.db import transaction

from comun.geografia import api as geografia
from comun.tipologias.constantes import AGRUPADOR
from dominios.entidades.models import Direccion
from dominios.entidades.repository import direccion as repo
from dominios.entidades.services import _comun


def _validar_ubicacion(ubicacion_id: int | None) -> None:
    if ubicacion_id is None:
        return
    if geografia.obtener_ubicacion(ubicacion_id) is None:
        raise ValidationError(f"No existe la ubicación geográfica {ubicacion_id}.")


@transaction.atomic
def crear(
    *,
    entidad_id: int,
    tipo_id: int,
    estado_id: int,
    calle: str = "",
    numero: str = "",
    descripcion: str = "",
    ubicacion_geografica_id: int | None = None,
    direccion_texto: str = "",
    latitud=None,
    longitud=None,
) -> Direccion:
    _comun.entidad(entidad_id)
    _comun.validar_tipo(tipo_id, AGRUPADOR.TIPO_DIRECCION)
    _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)
    _validar_ubicacion(ubicacion_geografica_id)

    return repo.crear(
        entidad_id=entidad_id,
        tipo_id=tipo_id,
        calle=calle,
        numero=numero,
        descripcion=descripcion,
        ubicacion_geografica_id=ubicacion_geografica_id,
        direccion_texto=direccion_texto,
        latitud=latitud,
        longitud=longitud,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    direccion_id: int,
    *,
    tipo_id: int | None = None,
    calle: str | None = None,
    numero: str | None = None,
    descripcion: str | None = None,
    ubicacion_geografica_id: int | None = None,
    direccion_texto: str | None = None,
    latitud=None,
    longitud=None,
    estado_id: int | None = None,
) -> Direccion:
    fila = repo.obtener(direccion_id)
    if fila is None:
        raise ValidationError(f"No existe la dirección {direccion_id}.")

    if tipo_id is not None:
        _comun.validar_tipo(tipo_id, AGRUPADOR.TIPO_DIRECCION)
    if estado_id is not None:
        _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)
    _validar_ubicacion(ubicacion_geografica_id)

    campos = _comun.solo_los_dados(
        tipo_id=tipo_id,
        calle=calle,
        numero=numero,
        descripcion=descripcion,
        ubicacion_geografica_id=ubicacion_geografica_id,
        direccion_texto=direccion_texto,
        latitud=latitud,
        longitud=longitud,
        estado_id=estado_id,
    )
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(direccion_id: int) -> Direccion:
    fila = repo.obtener(direccion_id)
    if fila is None:
        raise ValidationError(f"No existe la dirección {direccion_id}.")

    return repo.actualizar(fila, estado_id=_comun.estado_de_baja().pk)
