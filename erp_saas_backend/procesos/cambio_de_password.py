"""La persona cambia su propia contraseña y queda adentro.

Cruza dos familias —usuarios escribe la clave, seguridad corta las sesiones—
así que la transacción vive acá.
"""

from django.db import transaction

from comun.usuarios import api as usuarios
from dominios.seguridad import api as seguridad


@transaction.atomic
def cambiar(
    *, usuario_id: int, sesion_id: int | None, password_actual: str, password_nueva: str
):
    """Cierra las demás sesiones de esa cuenta y deja viva la que llama.

    Si la clave se filtró, cambiarla sin echar a quien la esté usando no
    sirve de nada. La propia se conserva para no obligar a entrar de nuevo
    justo después de cumplir con lo que el sistema pidió."""
    usuario = usuarios.cambiar_password(
        usuario_id=usuario_id,
        password_actual=password_actual,
        password_nueva=password_nueva,
    )
    seguridad.cerrar_sesiones_de(usuario_id, excepto_id=sesion_id)
    return usuario


__all__ = ["cambiar"]
