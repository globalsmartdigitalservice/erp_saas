"""Las mutations de los procesos que cruzan varias familias.

Viven acá y no en la app de cada uno porque ningún dominio importa
`procesos/`: la dependencia va en un solo sentido.
"""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import (
    requiere_autenticacion,
    requiere_permiso,
    usuario_de_la_sesion,
)
from procesos import cambio_de_password, reseteo_de_password

from .inputs import CambiarMiPasswordInput, ResetearPasswordInput


def _traducir(error: ValidationError) -> GraphQLError:
    return GraphQLError("; ".join(error.messages))


@strawberry.type
class CambioDePasswordMutations:
    """SIN `@auto_permisos`, a propósito: cambiar la propia contraseña no es
    administrar, es higiene. Con la marca, el catálogo generaría un permiso
    que nadie comprueba."""

    @strawberry.mutation(
        description=(
            "Cambia MI contraseña, sabiendo la anterior. No recibe id: la "
            "persona sale de la sesión. Cierra mis otras sesiones."
        )
    )
    @requiere_autenticacion
    def cambiar_mi_password(
        self, info: strawberry.Info, datos: CambiarMiPasswordInput
    ) -> bool:
        peticion = info.context.request
        try:
            cambio_de_password.cambiar(
                usuario_id=usuario_de_la_sesion(info).pk,
                sesion_id=getattr(peticion, "sesion_id", None),
                password_actual=datos.password_actual,
                password_nueva=datos.password_nueva,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return True


@auto_permisos(recurso="SEGU_MIEMBROS")
@strawberry.type
class ReseteoDePasswordMutations:
    @strawberry.mutation(
        description=(
            "Le devuelve el acceso a alguien de la empresa activa y responde "
            "la contraseña en claro. Es la ÚNICA vez que se puede leer. "
            "Cierra todas las sesiones de esa cuenta."
        )
    )
    @requiere_permiso
    def resetear_password(
        self, info: strawberry.Info, datos: ResetearPasswordInput
    ) -> str:
        try:
            hecho = reseteo_de_password.resetear(
                membresia_id=int(datos.membresia_id), password=datos.password
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return hecho.password


@strawberry.type
class ProcesosMutation(CambioDePasswordMutations, ReseteoDePasswordMutations):
    pass
