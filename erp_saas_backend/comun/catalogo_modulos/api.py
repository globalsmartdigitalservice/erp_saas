"""Superficie pública de `catalogo_modulos`. Catálogo del proveedor: sin `empresaId`."""

from comun.catalogo_modulos.models import (
    Funcionalidad,
    ModuloDependencia,
    ModuloSistema,
    SubModulo,
)
from comun.catalogo_modulos.repository import funcionalidad as _repo_func
from comun.catalogo_modulos.repository import modulo_dependencia as _repo_dep
from comun.catalogo_modulos.repository import modulo_sistema as _repo
from comun.catalogo_modulos.repository import sub_modulo as _repo_sub
from comun.catalogo_modulos.services import funcionalidad as _svc_func
from comun.catalogo_modulos.services import modulo_dependencia as _svc_dep
from comun.catalogo_modulos.services import modulo_sistema as _svc
from comun.catalogo_modulos.services import sub_modulo as _svc_sub


def obtener(modulo_id: int) -> ModuloSistema | None:
    return _repo.obtener(modulo_id)


def obtener_varios(modulo_ids) -> dict[int, ModuloSistema]:
    return _repo.obtener_varios(modulo_ids)


def obtener_por_codigo(codigo: str) -> ModuloSistema | None:
    return _repo.obtener_por_codigo(codigo)


def listar(solo_vendibles: bool = False) -> list[ModuloSistema]:
    return _repo.listar(solo_vendibles)


def crear(**campos) -> ModuloSistema:
    return _svc.crear(**campos)


def actualizar(modulo_id: int, **campos) -> ModuloSistema:
    return _svc.actualizar(modulo_id, **campos)


def desactivar(modulo_id: int) -> ModuloSistema:
    return _svc.desactivar(modulo_id)


def cadena_de(modulo_id: int) -> list[int]:
    """Lo que ese módulo necesita, directo e indirecto."""
    return _svc_dep.cadena_de(modulo_id)


def dependencias_directas_de(modulo_id: int) -> list[ModuloDependencia]:
    return _repo_dep.listar_de(modulo_id)


def dependen_de(modulo_id: int) -> list[ModuloDependencia]:
    """Al revés: quién se rompería si este módulo se da de baja."""
    return _repo_dep.listar_que_dependen_de(modulo_id)


def declarar_dependencia(**campos) -> ModuloDependencia:
    return _svc_dep.declarar(**campos)


def obtener_sub_modulo(sub_modulo_id: int) -> SubModulo | None:
    return _repo_sub.obtener(sub_modulo_id)


def obtener_sub_modulos(sub_modulo_ids) -> dict[int, SubModulo]:
    return _repo_sub.obtener_varios(sub_modulo_ids)


def obtener_sub_modulo_por_codigo(codigo: str) -> SubModulo | None:
    return _repo_sub.obtener_por_codigo(codigo)


def listar_sub_modulos(estado_id: int | None = None) -> list[SubModulo]:
    return _repo_sub.listar(estado_id)


def listar_sub_modulos_de(
    modulo_id: int, estado_id: int | None = None
) -> list[SubModulo]:
    return _repo_sub.listar_de_modulo(modulo_id, estado_id)


def listar_sub_modulos_de_varios(
    modulo_ids, estado_id: int | None = None
) -> list[SubModulo]:
    """En una consulta: sin esto, el menú hace una por módulo contratado."""
    return _repo_sub.listar_de_modulos(modulo_ids, estado_id)


def crear_sub_modulo(**campos) -> SubModulo:
    return _svc_sub.crear(**campos)


def actualizar_sub_modulo(sub_modulo_id: int, **campos) -> SubModulo:
    return _svc_sub.actualizar(sub_modulo_id, **campos)


def desactivar_sub_modulo(sub_modulo_id: int) -> SubModulo:
    return _svc_sub.desactivar(sub_modulo_id)


def obtener_funcionalidad(funcionalidad_id: int) -> Funcionalidad | None:
    return _repo_func.obtener(funcionalidad_id)


def obtener_funcionalidades(funcionalidad_ids) -> dict[int, Funcionalidad]:
    return _repo_func.obtener_varias(funcionalidad_ids)


def listar_funcionalidades(estado_id: int | None = None) -> list[Funcionalidad]:
    return _repo_func.listar(estado_id)


def listar_funcionalidades_de(
    sub_modulo_id: int, estado_id: int | None = None
) -> list[Funcionalidad]:
    return _repo_func.listar_de_sub_modulo(sub_modulo_id, estado_id)


def listar_funcionalidades_de_varios(
    sub_modulo_ids, estado_id: int | None = None
) -> list[Funcionalidad]:
    return _repo_func.listar_de_sub_modulos(sub_modulo_ids, estado_id)


def funcionalidad_del_permiso(auth_permission_id: int) -> Funcionalidad | None:
    return _repo_func.obtener_por_permiso(auth_permission_id)


def crear_funcionalidad(**campos) -> Funcionalidad:
    return _svc_func.crear(**campos)


def actualizar_funcionalidad(funcionalidad_id: int, **campos) -> Funcionalidad:
    return _svc_func.actualizar(funcionalidad_id, **campos)


def desactivar_funcionalidad(funcionalidad_id: int) -> Funcionalidad:
    """No le quita el permiso a nadie: solo la saca del menú. La asignación
    vive en `Grupo_Empresa_Permiso`."""
    return _svc_func.desactivar(funcionalidad_id)


def quitar_dependencia(modulo_id: int, depende_de_id: int) -> None:
    return _svc_dep.quitar(modulo_id, depende_de_id)
