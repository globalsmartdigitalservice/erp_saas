from django.core.exceptions import ValidationError
from django.db import transaction

from comun.catalogo_modulos.models import SubModulo
from comun.catalogo_modulos.repository import funcionalidad as repo_func
from comun.catalogo_modulos.repository import modulo_sistema as repo_modulo
from comun.catalogo_modulos.repository import sub_modulo as repo
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )


def _normalizar_codigo(codigo: str) -> str:
    return (codigo or "").strip().upper()


def _normalizar_ruta(ruta: str) -> str:
    ruta = (ruta or "").strip().lower()
    if len(ruta) > 1:
        ruta = ruta.rstrip("/")
    return ruta


def _validar_codigo(codigo: str, excluir_id: int | None = None) -> None:
    if not codigo:
        raise ValidationError("El código del submódulo no puede ir vacío.")
    if repo.existe_codigo(codigo, excluir_id):
        raise ValidationError(f"Ya existe un submódulo con el código '{codigo}'.")


def _validar_ruta(ruta: str, excluir_id: int | None = None) -> None:
    if not ruta:
        raise ValidationError(
            "La ruta del submódulo no puede ir vacía: es la dirección de la "
            "pantalla y es lo que usa el menú."
        )
    if not ruta.startswith("/"):
        raise ValidationError(f"La ruta tiene que empezar con '/'. Recibido: '{ruta}'.")
    if repo.existe_ruta(ruta, excluir_id):
        raise ValidationError(
            f"Ya hay un submódulo con la ruta '{ruta}'. Dos pantallas con la "
            f"misma dirección dejan el menú con dos entradas al mismo lado."
        )


def _validar_nombre(
    modulo_id: int, nombre: str, excluir_id: int | None = None
) -> None:
    if repo.existe_nombre_en_modulo(modulo_id, nombre, excluir_id):
        raise ValidationError(
            f"Ese módulo ya tiene un submódulo llamado '{nombre}'."
        )


@transaction.atomic
def crear(
    *,
    codigo: str,
    modulo_sistema_id: int,
    nombre: str,
    ruta: str,
    estado_id: int,
) -> SubModulo:
    _validar_estado(estado_id)

    if repo_modulo.obtener(modulo_sistema_id) is None:
        raise ValidationError(f"No existe el módulo {modulo_sistema_id}.")

    codigo = _normalizar_codigo(codigo)
    _validar_codigo(codigo)

    ruta = _normalizar_ruta(ruta)
    _validar_ruta(ruta)

    _validar_nombre(modulo_sistema_id, nombre)

    return repo.crear(
        codigo=codigo,
        modulo_sistema_id=modulo_sistema_id,
        nombre=nombre,
        ruta=ruta,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    sub_modulo_id: int,
    *,
    codigo: str | None = None,
    nombre: str | None = None,
    ruta: str | None = None,
    estado_id: int | None = None,
) -> SubModulo:
    fila = repo.obtener(sub_modulo_id)
    if fila is None:
        raise ValidationError(f"No existe el submódulo {sub_modulo_id}.")

    if estado_id is not None:
        _validar_estado(estado_id)

    if codigo is not None:
        codigo = _normalizar_codigo(codigo)
        _validar_codigo(codigo, excluir_id=sub_modulo_id)

    if ruta is not None:
        ruta = _normalizar_ruta(ruta)
        _validar_ruta(ruta, excluir_id=sub_modulo_id)

    if nombre is not None:
        _validar_nombre(fila.modulo_sistema_id, nombre, excluir_id=sub_modulo_id)

    # `modulo_sistema` NO se puede cambiar acá a propósito: mover una
    # pantalla de módulo cambia qué clientes la ven —depende de lo que
    # tengan contratado— y no es una edición, es una migración.
    campos = {
        campo: valor
        for campo, valor in (
            ("codigo", codigo),
            ("nombre", nombre),
            ("ruta", ruta),
            ("estado_id", estado_id),
        )
        if valor is not None
    }
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(sub_modulo_id: int) -> SubModulo:
    fila = repo.obtener(sub_modulo_id)
    if fila is None:
        raise ValidationError(f"No existe el submódulo {sub_modulo_id}.")

    acciones = repo_func.listar_de_sub_modulo(sub_modulo_id)
    if acciones:
        nombres = sorted(a.nombre for a in acciones)
        raise ValidationError(
            f"No se puede dar de baja '{fila.codigo}': todavía tiene "
            f"{len(acciones)} funcionalidad(es) — {', '.join(nombres)}. "
            f"Dalas de baja primero."
        )

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Ejecute: python manage.py cargar_semillas"
        )

    return repo.actualizar(fila, estado_id=baja.pk)
