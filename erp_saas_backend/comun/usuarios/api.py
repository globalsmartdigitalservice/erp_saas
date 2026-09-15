"""Superficie pública de `usuarios`: la identidad, no la membresía.

Crear una cuenta no la mete en ninguna empresa —eso es `membresias.afiliar()`—
y de qué cliente es sale de la empresa de la sesión, nunca por parámetro.
"""

from django.contrib.auth import get_user_model

from comun.usuarios.repository import usuario as _repo
from comun.usuarios.services import usuario as _svc

Usuario = get_user_model()


def obtener_usuario(usuario_id: int):
    """SIN comprobar el cliente: para resolver a alguien que ya se sabe
    cuál es —el login, el nombre de una fila de membresía—. Lo que sale a
    una consulta pública va por `obtener_usuario_del_cliente`."""
    return _repo.obtener(usuario_id)


def obtener_usuario_del_cliente(usuario_id: int):
    """La cuenta, solo si es del cliente de la sesión. Levanta si no."""
    return _svc.obtener_del_cliente(usuario_id)


def obtener_usuarios(usuario_ids) -> dict[int, "Usuario"]:
    """
    Versión por lote. OBLIGATORIA.

    La consume la lista de usuarios de una empresa: `membresias` trae las
    filas y los nombres de las personas salen de acá, todos juntos.
    """
    return _repo.obtener_varios(usuario_ids)


def obtener_por_username(username: str):
    return _repo.obtener_por_username(username)


def obtener_por_email(email: str):
    """Sin distinguir mayúsculas."""
    return _repo.obtener_por_email(email)


def crear_usuario(**campos):
    """Alta en el sistema. Arranca con `debe_cambiar_password = True`."""
    return _svc.crear(**campos)


def generar_password_temporal() -> str:
    """Una contraseña de un solo uso, pensada para dictar por teléfono."""
    return _svc.generar_password_temporal()


def actualizar_usuario(usuario_id: int, **campos):
    """Datos personales. La contraseña NO se toca acá."""
    return _svc.actualizar_datos(usuario_id, **campos)


def cambiar_password(*, usuario_id: int, password_actual: str, password_nueva: str):
    """
    La persona cambia SU PROPIA contraseña, sabiendo la anterior. Es la
    regla del análisis funcional: nadie más se la cambia.
    """
    return _svc.cambiar_password(
        usuario_id=usuario_id,
        password_actual=password_actual,
        password_nueva=password_nueva,
    )


def resetear_password(usuario_id: int, password: str | None = None) -> tuple:
    """Le pone una contraseña sin saber la anterior. Devuelve la cuenta y la
    contraseña en claro, para dictarla una sola vez."""
    return _svc.resetear_password(usuario_id, password)


def desactivar_usuario(usuario_id: int):
    """Baja del sistema entero. Para sacarlo de UNA empresa: `membresias`."""
    return _svc.desactivar(usuario_id)


def reactivar_usuario(usuario_id: int):
    return _svc.reactivar(usuario_id)


__all__ = [
    "obtener_usuario",
    "obtener_usuario_del_cliente",
    "obtener_usuarios",
    "obtener_por_username",
    "obtener_por_email",
    "crear_usuario",
    "actualizar_usuario",
    "cambiar_password",
    "resetear_password",
    "desactivar_usuario",
    "reactivar_usuario",
]
