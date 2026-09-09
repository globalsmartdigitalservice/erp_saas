"""Lo que el frontend manda para crear o editar un usuario."""

import strawberry


@strawberry.input(name="CrearUsuarioInput")
class CrearUsuarioInput:
    username: str
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    seg_apellido: str = ""


@strawberry.input(name="ActualizarUsuarioInput")
class ActualizarUsuarioInput:
    """
    `username` NO está y no va a estar: cambiarlo rompe el rastro de quién
    hizo qué en los registros ya escritos.

    `password` tampoco: tiene su propia mutation, que exige la anterior.
    """

    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    seg_apellido: str | None = None


@strawberry.input(name="CambiarPasswordInput")
class CambiarPasswordInput:
    """
    La actual se pide siempre. Sin eso, cualquiera que agarre una sesión
    abierta le cambia la contraseña al dueño y lo deja afuera.
    """

    password_actual: str
    password_nueva: str
