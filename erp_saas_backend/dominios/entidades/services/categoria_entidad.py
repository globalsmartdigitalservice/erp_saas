from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias.constantes import AGRUPADOR
from dominios.entidades.models import CategoriaEntidad
from dominios.entidades.repository import categoria_entidad as repo
from dominios.entidades.services import _comun


def _validar_nombre(nombre: str, excluir_id: int | None = None) -> None:
    if repo.existe_nombre(nombre, excluir_id):
        raise ValidationError(
            f"Ya hay una categoría llamada '{nombre}' en esta empresa."
        )


def _validar_descuento(descuento) -> None:
    if descuento is not None and Decimal(descuento) < 0:
        raise ValidationError(
            f"El descuento no puede ser negativo ({descuento}). Un descuento "
            f"negativo sería un recargo, y eso no es lo que este campo dice."
        )


@transaction.atomic
def crear(
    *,
    nombre: str,
    estado_id: int,
    descripcion: str = "",
    descuento_categ_cliente=0,
    lista_precio_id: int | None = None,
) -> CategoriaEntidad:
    _validar_nombre(nombre)
    _validar_descuento(descuento_categ_cliente)
    _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)

    return repo.crear(
        nombre=nombre,
        descripcion=descripcion,
        descuento_categ_cliente=descuento_categ_cliente,
        lista_precio_id=lista_precio_id,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    categoria_id: int,
    *,
    nombre: str | None = None,
    descripcion: str | None = None,
    descuento_categ_cliente=None,
    lista_precio_id: int | None = None,
    estado_id: int | None = None,
) -> CategoriaEntidad:
    fila = repo.obtener(categoria_id)
    if fila is None:
        raise ValidationError(f"No existe la categoría {categoria_id}.")

    if nombre is not None:
        _validar_nombre(nombre, excluir_id=categoria_id)
    _validar_descuento(descuento_categ_cliente)
    if estado_id is not None:
        _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)

    campos = _comun.solo_los_dados(
        nombre=nombre,
        descripcion=descripcion,
        descuento_categ_cliente=descuento_categ_cliente,
        lista_precio_id=lista_precio_id,
        estado_id=estado_id,
    )
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(categoria_id: int) -> CategoriaEntidad:
    """
    No se borra ni cuando no la usa nadie: `Rol_Entidad.categoria_entidad`
    es PROTECT, así que una categoría con clientes encima no se podría
    borrar nunca. Darla de baja la saca del combo y deja las de antes.
    """
    fila = repo.obtener(categoria_id)
    if fila is None:
        raise ValidationError(f"No existe la categoría {categoria_id}.")

    return repo.actualizar(fila, estado_id=_comun.estado_de_baja().pk)
