"""Las consultas de usuarios."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from comun.membresias import api as membresias
from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import (
    requiere_autenticacion,
    requiere_permiso,
)

from .types import UsuarioType


@strawberry.type
class UsuarioQueries:
    @strawberry.field(
        description=(
            "La ficha de alguien que trabaja en la empresa activa. Para la "
            "lista completa use `miembros`."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_usuarios_ver")
    @auto_permisos(recurso="SEGU_USUARIOS", operacion="ver")
    def usuario(self, info: strawberry.Info, id: strawberry.ID) -> UsuarioType | None:
        try:
            fila = membresias.persona_de_la_empresa(int(id))
        except ValidationError as error:
            codigo = getattr(error, "code", None)
            raise GraphQLError(
                "; ".join(error.messages),
                extensions={"code": codigo} if codigo else None,
            ) from error
        return UsuarioType.desde_modelo(fila)


@strawberry.type
class UsuarioQuery(UsuarioQueries):
    pass
