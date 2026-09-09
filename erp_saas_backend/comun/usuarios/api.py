"""
Superficie pública de `usuarios`. El resto de la app es privado.

    from comun.usuarios import api as usuarios

    juan = usuarios.crear_usuario(
        username="juan", email="juan@acme.com", password="...",
    )

 ESTA APP ES LA IDENTIDAD, NO LA MEMBRESÍA.

Crear un usuario NO lo mete en ninguna empresa: para eso está
`comun.membresias.afiliar()`. Son dos pasos a propósito — la misma
persona trabaja en varias empresas y su cuenta es una sola
.

Y no lleva filtro por empresa: es identidad global. La pantalla
"usuarios de mi empresa" NO sale de acá, sale de `membresias`, que sí
filtra.
"""

from django.contrib.auth import get_user_model

from comun.usuarios.repository import usuario as _repo
from comun.usuarios.services import usuario as _svc

Usuario = get_user_model()


def obtener_usuario(usuario_id: int):
    return _repo.obtener(usuario_id)


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


def desactivar_usuario(usuario_id: int):
    """Baja del sistema entero. Para sacarlo de UNA empresa: `membresias`."""
    return _svc.desactivar(usuario_id)


def reactivar_usuario(usuario_id: int):
    return _svc.reactivar(usuario_id)


__all__ = [
    "obtener_usuario",
    "obtener_usuarios",
    "obtener_por_username",
    "obtener_por_email",
    "crear_usuario",
    "actualizar_usuario",
    "cambiar_password",
    "desactivar_usuario",
    "reactivar_usuario",
]
