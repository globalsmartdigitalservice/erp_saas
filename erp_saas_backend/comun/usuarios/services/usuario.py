from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from comun.usuarios.repository import usuario as repo

Usuario = get_user_model()


def _normalizar_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalizar_username(username: str) -> str:
    return (username or "").strip()


def _validar_username(username: str, excluir_id: int | None = None) -> None:
    if not username:
        raise ValidationError("El nombre de usuario no puede ir vacío.")
    if repo.existe_username(username, excluir_id):
        raise ValidationError(f"Ya hay un usuario '{username}'.")


def _validar_email(email: str, excluir_id: int | None = None) -> None:
    if not email:
        raise ValidationError(
            "El correo es obligatorio: sin él no se puede resetear la "
            "contraseña de esta persona nunca más."
        )
    if repo.existe_email(email, excluir_id):
        raise ValidationError(f"Ya hay un usuario con el correo '{email}'.")


def _validar_password(password: str, usuario) -> None:
    """
    Los validadores de `settings.AUTH_PASSWORD_VALIDATORS`.

     Se le pasa el `usuario` y no solo la contraseña: es lo que permite
    rechazar "Mamani2026" para alguien apellidado Mamani. Sin ese segundo
    argumento, el validador de similitud no tiene con qué comparar y deja
    pasar todo.
    """
    validate_password(password, usuario)


@transaction.atomic
def crear(
    *,
    username: str,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    seg_apellido: str = "",
    debe_cambiar_password: bool = True,
) -> "Usuario":
    """
    Da de alta a una persona en el SISTEMA. No la afilia a ninguna
    empresa: eso es `membresias.afiliar()`, y son dos cosas distintas a
    propósito.
    """
    username = _normalizar_username(username)
    email = _normalizar_email(email)

    _validar_username(username)
    _validar_email(email)

    # El usuario se arma SIN guardar para que el validador de similitud
    # pueda comparar la contraseña contra el nombre y el correo.
    tentativa = Usuario(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        seg_apellido=seg_apellido,
    )
    _validar_password(password, tentativa)

    return repo.crear(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        seg_apellido=seg_apellido,
        debe_cambiar_password=debe_cambiar_password,
    )


@transaction.atomic
def actualizar_datos(
    usuario_id: int,
    *,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    seg_apellido: str | None = None,
) -> "Usuario":
    """
    Los datos personales. **La contraseña NO se toca acá** — ver
    `cambiar_password`. Y `username` tampoco: cambiarlo rompe el rastro
    de quién hizo qué en los registros ya escritos.
    """
    usuario = repo.obtener(usuario_id)
    if usuario is None:
        raise ValidationError(f"No existe el usuario {usuario_id}.")

    if email is not None:
        email = _normalizar_email(email)
        _validar_email(email, excluir_id=usuario_id)

    campos = {
        campo: valor
        for campo, valor in (
            ("email", email),
            ("first_name", first_name),
            ("last_name", last_name),
            ("seg_apellido", seg_apellido),
        )
        if valor is not None
    }
    if not campos:
        return usuario

    return repo.actualizar(usuario, **campos)


@transaction.atomic
def cambiar_password(
    *, usuario_id: int, password_actual: str, password_nueva: str
) -> "Usuario":
    """
    La persona cambia SU PROPIA contraseña, y para eso tiene que saber la
    anterior.

     Exigir la actual no es burocracia: sin eso, cualquiera que agarre
    una sesión abierta —una pantalla sin bloquear— le cambia la
    contraseña al dueño y lo deja afuera de su propia cuenta.

    Es la regla del análisis funcional: *"lo único que puede cambiar contraseña
    es el mismo usuario"*.
    """
    usuario = repo.obtener(usuario_id)
    if usuario is None:
        raise ValidationError(f"No existe el usuario {usuario_id}.")

    if not usuario.check_password(password_actual):
        raise ValidationError("La contraseña actual no es correcta.")

    if password_actual == password_nueva:
        raise ValidationError("La contraseña nueva tiene que ser distinta.")

    _validar_password(password_nueva, usuario)

    usuario.set_password(password_nueva)
    # Se apaga acá: ya la cambió, que era lo que se le estaba pidiendo.
    usuario.debe_cambiar_password = False
    usuario.save(update_fields=["password", "debe_cambiar_password"])
    return usuario


@transaction.atomic
def desactivar(usuario_id: int) -> "Usuario":
    """
    Baja del SISTEMA entero: no entra a ninguna empresa.

    Distinto de `membresias.desafiliar()`, que lo saca de UNA. Acá el
    soft delete es `is_active` de Django, no una `Tipologia`: esta tabla
    es capa 2 y no puede depender de `comun/tipologias`.
    """
    usuario = repo.obtener(usuario_id)
    if usuario is None:
        raise ValidationError(f"No existe el usuario {usuario_id}.")

    return repo.actualizar(usuario, is_active=False)


@transaction.atomic
def reactivar(usuario_id: int) -> "Usuario":
    usuario = repo.obtener(usuario_id)
    if usuario is None:
        raise ValidationError(f"No existe el usuario {usuario_id}.")

    return repo.actualizar(usuario, is_active=True)
