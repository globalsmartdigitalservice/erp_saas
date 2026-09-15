from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction

from comun.catalogo_modulos.models import Funcionalidad
from comun.catalogo_modulos.repository import funcionalidad as repo
from comun.catalogo_modulos.repository import sub_modulo as repo_sub
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )


def _validar_permiso(auth_permission_id: int, excluir_id: int | None = None) -> None:
    if not Permission.objects.filter(pk=auth_permission_id).exists():
        raise ValidationError(f"No existe el permiso {auth_permission_id}.")

    if repo.existe_permiso(auth_permission_id, excluir_id):
        ya = repo.obtener_por_permiso(auth_permission_id)
        raise ValidationError(
            f"Ese permiso ya está descrito por la funcionalidad '{ya.nombre}'. "
            f"Un permiso va en una sola: si estuviera en dos, quien arma un rol "
            f"lo vería repetido y no sabría cuál marcar."
        )


def _validar_nombre(
    sub_modulo_id: int, nombre: str, excluir_id: int | None = None
) -> None:
    if repo.existe_nombre_en_sub_modulo(sub_modulo_id, nombre, excluir_id):
        raise ValidationError(
            f"Esa pantalla ya tiene una funcionalidad llamada '{nombre}'."
        )


@transaction.atomic
def crear(
    *,
    sub_modulo_id: int,
    auth_permission_id: int,
    nombre: str,
    estado_id: int,
    descripcion: str = "",
) -> Funcionalidad:
    _validar_estado(estado_id)

    if repo_sub.obtener(sub_modulo_id) is None:
        raise ValidationError(f"No existe el submódulo {sub_modulo_id}.")

    _validar_permiso(auth_permission_id)
    _validar_nombre(sub_modulo_id, nombre)

    return repo.crear(
        sub_modulo_id=sub_modulo_id,
        auth_permission_id=auth_permission_id,
        nombre=nombre,
        descripcion=descripcion,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    funcionalidad_id: int,
    *,
    nombre: str | None = None,
    descripcion: str | None = None,
    sub_modulo_id: int | None = None,
    estado_id: int | None = None,
) -> Funcionalidad:
    fila = repo.obtener(funcionalidad_id)
    if fila is None:
        raise ValidationError(f"No existe la funcionalidad {funcionalidad_id}.")

    if estado_id is not None:
        _validar_estado(estado_id)

    # Mover una acción de pantalla sí se permite: el permiso no cambia.
    destino = sub_modulo_id if sub_modulo_id is not None else fila.sub_modulo_id
    if sub_modulo_id is not None and repo_sub.obtener(sub_modulo_id) is None:
        raise ValidationError(f"No existe el submódulo {sub_modulo_id}.")

    if nombre is not None:
        _validar_nombre(destino, nombre, excluir_id=funcionalidad_id)

    # `auth_permission` NO se cambia: los grupos que ya lo tenían
    # asignado quedarían describiendo algo que nadie les dio.
    campos = {
        campo: valor
        for campo, valor in (
            ("nombre", nombre),
            ("descripcion", descripcion),
            ("sub_modulo_id", sub_modulo_id),
            ("estado_id", estado_id),
        )
        if valor is not None
    }
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(funcionalidad_id: int) -> Funcionalidad:
    """Soft delete sin condiciones. Dar de baja la funcionalidad NO le
    quita el permiso a nadie: eso se hace en el grupo."""
    fila = repo.obtener(funcionalidad_id)
    if fila is None:
        raise ValidationError(f"No existe la funcionalidad {funcionalidad_id}.")

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Ejecute: python manage.py cargar_semillas"
        )

    return repo.actualizar(fila, estado_id=baja.pk)


def borrar(funcionalidad_id: int) -> None:
    """Borrado DE VERDAD, y es a propósito: esta fila es derivada.

    La crea `generar_permisos` para ponerle nombre y pantalla a un permiso,
    así que cuando el permiso desaparece del código no queda nada que
    describir. Para sacarla del menú sin borrarla está `desactivar`."""
    fila = repo.obtener(funcionalidad_id)
    if fila is None:
        raise ValidationError(f"No existe la funcionalidad {funcionalidad_id}.")

    fila.delete()
