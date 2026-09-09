from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias.constantes import AGRUPADOR
from dominios.entidades.models import RolEntidad
from dominios.entidades.repository import categoria_entidad as repo_categoria
from dominios.entidades.repository import rol_entidad as repo
from dominios.entidades.services import _comun


def _validar_categoria(categoria_id: int | None) -> None:
    """
    LA DEFENSA DEL AISLAMIENTO. `repo_categoria.obtener()` consulta por el manager
    tenant, así que una categoría de otra empresa devuelve `None` — y el
    mensaje dice "no existe", no "no es tuya": enterarse de que el id 412
    existe en otra empresa ya sería una filtración.
    """
    if categoria_id is None:
        return
    if repo_categoria.obtener(categoria_id) is None:
        raise ValidationError(f"No existe la categoría {categoria_id}.")


def _validar_limite(limite) -> None:
    if limite is not None and Decimal(limite) < 0:
        raise ValidationError(
            f"El límite de crédito no puede ser negativo ({limite})."
        )


@transaction.atomic
def crear(
    *,
    entidad_id: int,
    tipo_rol_id: int,
    estado_id: int,
    categoria_entidad_id: int | None = None,
    limite_credito=None,
    datos_rol: dict | None = None,
) -> RolEntidad:
    _comun.entidad(entidad_id)
    _comun.validar_tipo(tipo_rol_id, AGRUPADOR.TIPO_ROL)
    _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)
    _validar_categoria(categoria_entidad_id)
    _validar_limite(limite_credito)

    if repo.existe(entidad_id, tipo_rol_id):
        raise ValidationError(
            "Esa entidad ya tiene ese rol. Un rol se asigna una sola vez; "
            "si desea cambiar la categoría o el límite, actualícelo."
        )

    return repo.crear(
        entidad_id=entidad_id,
        tipo_rol_id=tipo_rol_id,
        categoria_entidad_id=categoria_entidad_id,
        limite_credito=limite_credito,
        datos_rol=datos_rol if datos_rol is not None else {},
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    rol_id: int,
    *,
    categoria_entidad_id: int | None = None,
    limite_credito=None,
    datos_rol: dict | None = None,
    estado_id: int | None = None,
) -> RolEntidad:
    """
    `entidad` y `tipo_rol` NO se pueden cambiar: son lo que ese rol ES.
    Cambiar cualquiera de los dos es borrar este rol y crear otro, y así
    conviene que se lea en el código que lo llame.
    """
    fila = repo.obtener(rol_id)
    if fila is None:
        raise ValidationError(f"No existe el rol {rol_id}.")

    if estado_id is not None:
        _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)
    _validar_categoria(categoria_entidad_id)
    _validar_limite(limite_credito)

    campos = _comun.solo_los_dados(
        categoria_entidad_id=categoria_entidad_id,
        limite_credito=limite_credito,
        datos_rol=datos_rol,
        estado_id=estado_id,
    )
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(rol_id: int) -> RolEntidad:
    """La entidad sigue existiendo; deja de actuar en ese papel."""
    fila = repo.obtener(rol_id)
    if fila is None:
        raise ValidationError(f"No existe el rol {rol_id}.")

    return repo.actualizar(fila, estado_id=_comun.estado_de_baja().pk)
