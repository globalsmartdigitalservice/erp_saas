import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas import api as empresas
from comun.usuarios.repository import usuario as repo
from core.tenancy import empresa_actual

Usuario = get_user_model()


ALFABETO_DICTABLE = "abcdefghjkmnpqrstuvwxyz23456789"

_LARGO_DEL_GRUPO = 4
_GRUPOS = 3


def generar_password_temporal() -> str:
    """Una contraseña de un solo uso, para dictar: `k7pm-q3wx-t9fh`.

    La usan el alta de un cliente y el reseteo del administrador. Nunca se
    guarda en claro: se muestra una vez y quien la recibe está obligado a
    cambiarla en el primer ingreso."""
    grupos = (
        "".join(secrets.choice(ALFABETO_DICTABLE) for _ in range(_LARGO_DEL_GRUPO))
        for _ in range(_GRUPOS)
    )
    return "-".join(grupos)


def _normalizar_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalizar_username(username: str) -> str:
    return (username or "").strip()


def _validar_username(username: str, excluir_id: int | None = None) -> None:
    if not username:
        raise ValidationError("El nombre de usuario no puede ir vacío.")
    if repo.existe_username(username, excluir_id):
        raise ValidationError(f"Ya hay un usuario '{username}'.")


def _validar_email(
    email: str, matriz_id: int | None, excluir_id: int | None = None
) -> None:
    if not email:
        raise ValidationError(
            "El correo es obligatorio: sin él no se puede resetear la "
            "contraseña de esta persona nunca más."
        )
    if repo.existe_email(email, matriz_id, excluir_id):
        raise ValidationError(f"Ya hay un usuario con el correo '{email}'.")


def _matriz_del_contexto():
    """De qué cliente es la cuenta que se está creando.

    No se recibe por parámetro y no es un descuido: si el que llama pudiera
    elegirla, un administrador podría crear cuentas en otro cliente.
    """
    empresa_id = empresa_actual()
    if empresa_id is None:
        raise ValidationError(
            "No hay empresa en la sesión: no se sabe de qué cliente sería "
            "esta cuenta."
        )

    matriz = empresas.matriz_de(empresa_id)
    if matriz is None:
        raise ValidationError(f"No existe la empresa {empresa_id}.")
    return matriz


def obtener_del_cliente(usuario_id: int) -> "Usuario":
    """La cuenta, solo si es del cliente de la sesión.

     El mismo mensaje que si no existiera: decir "no tiene permiso sobre
    el usuario 7" confirma que el 7 existe, y probando números se arma el
    padrón.
    """
    usuario = repo.obtener(usuario_id)
    if usuario is None or usuario.matriz_id != _matriz_del_contexto().pk:
        raise ValidationError(f"No existe el usuario {usuario_id}.")
    return usuario


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
    Da de alta a una persona en EL CLIENTE de la sesión. No la afilia a
    ninguna empresa: eso es `membresias.afiliar()`, y son dos cosas
    distintas a propósito.
    """
    username = _normalizar_username(username)
    email = _normalizar_email(email)
    matriz = _matriz_del_contexto()

    _validar_username(username)
    _validar_email(email, matriz.pk)

    
    tentativa = Usuario(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        seg_apellido=seg_apellido,
    )
    _validar_password(password, tentativa)

    return repo.crear(
        matriz=matriz,
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
    usuario = obtener_del_cliente(usuario_id)

    if email is not None:
        email = _normalizar_email(email)
        _validar_email(email, usuario.matriz_id, excluir_id=usuario_id)

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
    usuario = obtener_del_cliente(usuario_id)

    if not usuario.check_password(password_actual):
        raise ValidationError("La contraseña actual no es correcta.")

    if password_actual == password_nueva:
        raise ValidationError("La contraseña nueva tiene que ser distinta.")

    _validar_password(password_nueva, usuario)

    usuario.set_password(password_nueva)
  
    usuario.debe_cambiar_password = False
    usuario.save(update_fields=["password", "debe_cambiar_password"])
    return usuario


@transaction.atomic
def desactivar(usuario_id: int) -> "Usuario":
    """
    Baja del SISTEMA entero: no entra a ninguna empresa.

    Distinto de `membresias.desafiliar()`, que lo saca de UNA. Acá el
    soft delete es `is_active` de Django y no una `Tipologia`: lo miran el
    login y el middleware en cada petición, y una FK les agregaría una
    consulta a cambio de nada.
    """
    usuario = obtener_del_cliente(usuario_id)

    return repo.actualizar(usuario, is_active=False)


@transaction.atomic
def reactivar(usuario_id: int) -> "Usuario":
    usuario = obtener_del_cliente(usuario_id)

    return repo.actualizar(usuario, is_active=True)
