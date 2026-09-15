"""Lo que reciben las mutations de los procesos."""

import strawberry


@strawberry.input(name="CambiarMiPasswordInput")
class CambiarMiPasswordInput:
    """No lleva `id`: quién es sale de la sesión.

    La actual se pide siempre. Sin eso, cualquiera que agarre una pantalla
    sin bloquear le cambia la contraseña al dueño y lo deja afuera.
    """

    password_actual: str
    password_nueva: str


@strawberry.input(name="ResetearPasswordInput")
class ResetearPasswordInput:
    """Se identifica a la persona por su MEMBRESÍA en la empresa activa, no
    por el id de su cuenta: el encargado de una sucursal resetea a los suyos.

    Sin `password` se genera una temporal fácil de dictar.
    """

    membresia_id: strawberry.ID
    password: str | None = None
