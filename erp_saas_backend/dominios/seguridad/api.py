"""Superficie pública de `seguridad`. El resto de la app es privado.

    QUIÉN SOS          → comun/usuarios      (Usuario)
    DÓNDE TRABAJÁS     → comun/membresias    (Usuario_Empresa)
    QUÉ PODÉS HACER    → acá

Los roles BAJAN de la casa matriz a sus sucursales porque un rol es
configuración. Los datos no bajan: ésos siguen con filtro exacto."""

import datetime

from django.contrib.auth.models import Permission

from dominios.seguridad.models import (
    Dispositivo,
    DispositivoUsuario,
    GrupoEmpresa,
    GrupoEmpresaPermiso,
    GrupoUsuario,
    HorarioAcceso,
    HorarioExcepcion,
)
from dominios.seguridad.repository import acceso as _repo_acceso
from dominios.seguridad.repository import grupo_empresa as _repo
from dominios.seguridad.repository import grupo_usuario as _repo_asig
from dominios.seguridad.repository import permiso as _repo_permiso
from dominios.seguridad.services import grupo_empresa as _svc
from dominios.seguridad.services import acceso as _svc_acceso
from dominios.seguridad.services import dispositivos_y_horarios as _svc_eq
from dominios.seguridad.services import grupo_usuario as _svc_asig
from dominios.seguridad.services import login as _svc_login


def cerrar_sesiones_de(usuario_id: int, *, excepto_id: int | None = None) -> int:
    """Saca a una cuenta de todas sus empresas. Con `excepto_id` deja viva
    una: la de quien está cambiando su propia contraseña."""
    return _svc_login.cerrar_sesiones_de(usuario_id, excepto_id=excepto_id)


def obtener_rol(grupo_id: int) -> GrupoEmpresa | None:
    return _repo.obtener(grupo_id)


def obtener_roles(grupo_ids) -> dict[int, GrupoEmpresa]:
    return _repo.obtener_varios(grupo_ids)


def listar_roles(estado_id: int | None = None) -> list[GrupoEmpresa]:
    """Los que esta empresa puede usar: los suyos y los de su matriz."""
    return _repo.listar(estado_id)


def listar_roles_con_conteo(estado_id: int | None = None) -> list[GrupoEmpresa]:
    """Con `cantidad_permisos` ya contada: la pantalla de roles en dos
    consultas en vez de una por fila."""
    return _repo.listar_con_cantidad_de_permisos(estado_id)


def crear_rol(*, nombre: str, estado_id: int) -> GrupoEmpresa:
    """Se crea SIEMPRE en la empresa activa: `empresa` sale del contexto,
    no se recibe de afuera."""
    return _svc.crear(nombre=nombre, estado_id=estado_id)


def actualizar_rol(grupo_id: int, **campos) -> GrupoEmpresa:
    """Falla si el rol es de la casa matriz: solo el dueño lo edita."""
    return _svc.actualizar(grupo_id, **campos)


def desactivar_rol(grupo_id: int) -> GrupoEmpresa:
    """Falla si alguien todavía lo tiene asignado."""
    return _svc.desactivar(grupo_id)


def listar_permisos_del_rol(grupo_id: int) -> list[GrupoEmpresaPermiso]:
    return _repo.listar_permisos_de(grupo_id)


def listar_catalogo_de_permisos() -> list[Permission]:
    """Todos los permisos que existen, sin mirar quién los tiene."""
    return _repo_permiso.listar_catalogo()


def agregar_permiso(*, grupo_id: int, auth_permission_id: int):
    """Idempotente: marcarlo dos veces no falla ni duplica."""
    return _svc.agregar_permiso(
        grupo_id=grupo_id, auth_permission_id=auth_permission_id
    )


def quitar_permiso(*, grupo_id: int, auth_permission_id: int):
    """Idempotente: quitar lo que no estaba no es un error."""
    return _svc.quitar_permiso(
        grupo_id=grupo_id, auth_permission_id=auth_permission_id
    )


def obtener_asignacion(asignacion_id: int) -> GrupoUsuario | None:
    return _repo_asig.obtener(asignacion_id)


def obtener_asignaciones(asignacion_ids) -> dict[int, GrupoUsuario]:
    return _repo_asig.obtener_varias(asignacion_ids)


def historial_de(membresia_id: int) -> list[GrupoUsuario]:
    """Todos los roles que tuvo esa persona acá, vigentes y terminados."""
    return _repo_asig.listar_de_membresia(membresia_id)


def roles_de_varias_membresias(membresia_ids) -> list[GrupoUsuario]:
    """Los roles de VARIAS personas en UNA consulta."""
    return _repo_asig.listar_de_membresias(membresia_ids)


def roles_vigentes_de_varias_membresias(membresia_ids) -> list[GrupoUsuario]:
    """Los roles de hoy de varias personas, en una consulta."""
    return _svc_asig.roles_vigentes_de_varias(membresia_ids)


def exigir_que_quede_quien_administre(
    *, excluir_membresia_id: int | None = None, excluir_asignacion_id: int | None = None
) -> None:
    """Rechaza lo que dejaría a la empresa activa sin nadie que pueda asignar roles."""
    _svc_asig.exigir_que_quede_quien_administre(
        excluir_membresia_id=excluir_membresia_id,
        excluir_asignacion_id=excluir_asignacion_id,
    )


def asignar_rol(
    *,
    membresia_id: int,
    grupo_id: int,
    estado_id: int,
    fecha_inicio: datetime.date | None = None,
    fecha_fin: datetime.date | None = None,
    asignado_por_id: int | None = None,
    motivo: str = "",
) -> GrupoUsuario:
    """El rol puede ser de la casa matriz: es lo que permite definirlo una
    sola vez arriba y usarlo en las 20 sucursales."""
    return _svc_asig.asignar(
        membresia_id=membresia_id,
        grupo_id=grupo_id,
        estado_id=estado_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        asignado_por_id=asignado_por_id,
        motivo=motivo,
    )


def quitar_rol(
    *, asignacion_id: int, fecha_fin: datetime.date | None = None
) -> GrupoUsuario:
    """Le pone fecha de fin y lo da de baja. NO borra la fila: es historial."""
    return _svc_asig.quitar(asignacion_id=asignacion_id, fecha_fin=fecha_fin)


def actualizar_asignacion(asignacion_id: int, **campos) -> GrupoUsuario:
    """Solo fechas, motivo y estado: ni la persona ni el rol se cambian."""
    return _svc_asig.actualizar(asignacion_id, **campos)


def permisos_de(membresia_id: int) -> set[str]:
    """Los códigos que esa persona tiene HOY en esta empresa, en el formato
    de Django. Es lo que consume el backend de autenticación."""
    return _svc_asig.permisos_vigentes_de(membresia_id)


def puede_entrar(
    *,
    membresia_id: int,
    momento: datetime.datetime | None = None,
    mac: str | None = None,
    ip_publica: str | None = None,
):
    """El veredicto de acceso: horario + excepciones + equipo autorizado.

     NO reemplaza a la contraseña ni decide permisos: corre DESPUÉS de que
    la persona demostró quién es. "Puede entrar" no es "puede anular".
    """
    return _svc_acceso.puede_entrar(
        membresia_id=membresia_id,
        momento=momento,
        mac=mac,
        ip_publica=ip_publica,
    )


# ── Equipos ──


def obtener_dispositivo(dispositivo_id: int) -> Dispositivo | None:
    return _repo_acceso.obtener_dispositivo(dispositivo_id)


def obtener_dispositivos(dispositivo_ids) -> dict[int, Dispositivo]:
    return _repo_acceso.obtener_dispositivos(dispositivo_ids)


def listar_dispositivos(estado_id: int | None = None) -> list[Dispositivo]:
    """Los equipos de la empresa activa."""
    return _repo_acceso.listar_dispositivos(estado_id)


def registrar_dispositivo(**campos) -> Dispositivo:
    """Alta de un equipo en la empresa activa."""
    return _svc_eq.registrar_dispositivo(**campos)


def actualizar_dispositivo(dispositivo_id: int, **campos) -> Dispositivo:
    return _svc_eq.actualizar_dispositivo(dispositivo_id, **campos)


def autorizar_dispositivo(**campos) -> DispositivoUsuario:
    """Le autoriza un equipo a una persona DE ESTA EMPRESA."""
    return _svc_eq.autorizar_dispositivo(**campos)


def desautorizar_dispositivo(**campos) -> DispositivoUsuario:
    """Le pone fecha de fin. NO borra la fila: es historial."""
    return _svc_eq.desautorizar_dispositivo(**campos)


def dispositivos_de(membresia_id: int) -> list[DispositivoUsuario]:
    """Los equipos de una persona acá, autorizados y ya dados de baja."""
    return _repo_acceso.listar_autorizaciones(membresia_id)


# ── Horarios ──


def horarios_de(membresia_id: int) -> list[HorarioAcceso]:
    return _repo_acceso.listar_horarios(membresia_id)


def cargar_horario(**campos) -> HorarioAcceso:
    """`hora_fin` menor que `hora_inicio` es válido: turno que cruza la
    medianoche."""
    return _svc_eq.cargar_horario(**campos)


def quitar_horario(**campos) -> HorarioAcceso:
    return _svc_eq.quitar_horario(**campos)


# ── Excepciones ──


def excepciones_de(membresia_id: int) -> list[HorarioExcepcion]:
    return _repo_acceso.listar_excepciones(membresia_id)


def cargar_excepcion(**campos) -> HorarioExcepcion:
    """El día suelto: PERMISO deja entrar, BLOQUEO lo impide."""
    return _svc_eq.cargar_excepcion(**campos)


def quitar_excepcion(**campos) -> HorarioExcepcion:
    return _svc_eq.quitar_excepcion(**campos)


__all__ = [
    "cerrar_sesiones_de",
    "obtener_rol",
    "obtener_roles",
    "listar_roles",
    "listar_roles_con_conteo",
    "crear_rol",
    "actualizar_rol",
    "desactivar_rol",
    "listar_permisos_del_rol",
    "listar_catalogo_de_permisos",
    "agregar_permiso",
    "quitar_permiso",
    "obtener_asignacion",
    "obtener_asignaciones",
    "historial_de",
    "roles_de_varias_membresias",
    "roles_vigentes_de_varias_membresias",
    "exigir_que_quede_quien_administre",
    "asignar_rol",
    "quitar_rol",
    "actualizar_asignacion",
    "permisos_de",
    "puede_entrar",
    "obtener_dispositivo",
    "obtener_dispositivos",
    "listar_dispositivos",
    "registrar_dispositivo",
    "actualizar_dispositivo",
    "autorizar_dispositivo",
    "desautorizar_dispositivo",
    "dispositivos_de",
    "horarios_de",
    "cargar_horario",
    "quitar_horario",
    "excepciones_de",
    "cargar_excepcion",
    "quitar_excepcion",
]
