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


@strawberry.input(name="PersonaNuevaInput")
class PersonaNuevaInput:
    """Sin `password` se genera una temporal fácil de dictar."""

    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    seg_apellido: str = ""
    password: str | None = None


@strawberry.input(name="DarDeAltaMiembroInput")
class DarDeAltaMiembroInput:
    """`usuarioId` si la persona ya es del cliente, `persona` si hay que crearla: una de las dos."""

    usuario_id: strawberry.ID | None = None
    persona: PersonaNuevaInput | None = None
    rol_ids: list[strawberry.ID] = strawberry.field(default_factory=list)
