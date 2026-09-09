"""
Superficie pública de `membresias`. El resto de la app es privado.

Nadie de afuera importa `models`, `repository` ni `services`
.

Uso:

    from comun.membresias import api as membresias

    # el login, antes de saber en qué empresa estás
    donde_trabaja = membresias.empresas_de(usuario.pk)

    # el alta de todos los días
    membresias.afiliar(usuario_id=..., empresa_id=..., estado_id=...)

    # el gerente de la cadena, de una sola vez
    membresias.afiliar_al_grupo(usuario_id=..., empresa_id=matriz.pk, estado_id=...)

Las lecturas van directo al repository; las escrituras pasan siempre por
services, que es donde están los invariantes.
"""

import datetime

from comun.membresias.models import UsuarioEmpresa
from comun.membresias.repository import usuario_empresa as _repo
from comun.membresias.services import usuario_empresa as _svc


def obtener_membresia(membresia_id: int) -> UsuarioEmpresa | None:
    return _repo.obtener(membresia_id)


def obtener_membresias(membresia_ids) -> dict[int, UsuarioEmpresa]:
    return _repo.obtener_varias(membresia_ids)


def listar_membresias(estado_id: int | None = None) -> list[UsuarioEmpresa]:
    """Quiénes trabajan en la empresa del contexto."""
    return _repo.listar(estado_id)


def membresia_de(usuario_id: int) -> UsuarioEmpresa | None:
    """La membresía de esa persona en la empresa del contexto."""
    return _repo.obtener_de_usuario(usuario_id)


def empresas_de(usuario_id: int) -> list[UsuarioEmpresa]:
    """
    En qué empresas está dada de alta una persona.

     La consulta del LOGIN: corre ANTES de que haya empresa en el
    contexto, porque es justamente la que la averigua. Es lo que llena
    la pantalla "¿dónde querés trabajar?".

    Es la razón por la que esta app vive en `comun/` y no con los
    permisos en `dominios/seguridad/`.
    """
    return _repo.listar_de_usuario_en_todas_las_empresas(usuario_id)


def afiliar(
    *,
    usuario_id: int,
    empresa_id: int,
    fecha_asignacion: datetime.date | None = None,
    estado_id: int,
) -> UsuarioEmpresa:
    """Da de alta a una persona en UNA empresa."""
    return _svc.afiliar(
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        fecha_asignacion=fecha_asignacion,
        estado_id=estado_id,
    )


def afiliar_al_grupo(
    *,
    usuario_id: int,
    empresa_id: int,
    fecha_asignacion: datetime.date | None = None,
    estado_id: int,
) -> list[UsuarioEmpresa]:
    """
    Da de alta a una persona en una empresa y en TODAS sus sucursales.

    Devuelve solo las membresías creadas; donde ya estaba, se saltea.
    Es el "dar de alta en todo el grupo".
    """
    return _svc.afiliar_al_grupo(
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        fecha_asignacion=fecha_asignacion,
        estado_id=estado_id,
    )


def desafiliar(
    *,
    membresia_id: int,
    estado_baja_id: int,
    fecha_finalizacion: datetime.date | None = None,
) -> UsuarioEmpresa:
    """Soft delete: cambia el estado y pone la fecha de fin."""
    return _svc.desafiliar(
        membresia_id=membresia_id,
        estado_baja_id=estado_baja_id,
        fecha_finalizacion=fecha_finalizacion,
    )


def reactivar(*, membresia_id: int, estado_activo_id: int) -> UsuarioEmpresa:
    """El que se fue y volvió: se reactiva su fila, no se crea otra."""
    return _svc.reactivar(
        membresia_id=membresia_id, estado_activo_id=estado_activo_id
    )


__all__ = [
    "obtener_membresia",
    "obtener_membresias",
    "listar_membresias",
    "membresia_de",
    "empresas_de",
    "afiliar",
    "afiliar_al_grupo",
    "desafiliar",
    "reactivar",
]
