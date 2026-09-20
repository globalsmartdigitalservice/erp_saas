"""Las mutations de usuarios."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import (
    requiere_autenticacion,
    requiere_permiso,
)

from comun.membresias import api as membresias
from comun.usuarios import api as usuarios

from .inputs import ActualizarUsuarioInput
from .types import UsuarioType


def _traducir(error: ValidationError) -> GraphQLError:
    """
    Un `ValidationError` del dominio es un error ESPERADO: el mensaje va
    tal cual al cliente. Cualquier otra excepción sube sin tocar, para que
    no se disfrace un bug de error de validación (`core/graphql/errores.py`).
    """
    return GraphQLError("; ".join(error.messages))


@auto_permisos(recurso="SEGU_USUARIOS")
@strawberry.type
class UsuarioMutations:
    @strawberry.mutation(description="Los datos personales. La contraseña no.")
    @requiere_autenticacion
    @requiere_permiso("segu_usuarios_actualizar_usuario")
    def actualizar_usuario(
        self,
        info: strawberry.Info, id: strawberry.ID, datos: ActualizarUsuarioInput
    ) -> UsuarioType:
        try:
            persona = membresias.persona_de_la_empresa(int(id))
            fila = usuarios.actualizar_usuario(
                persona.pk,
                email=datos.email,
                first_name=datos.first_name,
                last_name=datos.last_name,
                seg_apellido=datos.seg_apellido,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return UsuarioType.desde_modelo(fila)


@strawberry.type
class UsuarioMutation(UsuarioMutations):
    pass
