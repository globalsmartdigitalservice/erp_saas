"""Las consultas de usuarios."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from comun.membresias import api as membresias
from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import requiere_permiso

from .types import UsuarioType


@auto_permisos(recurso="SEGU_USUARIOS")
@strawberry.type
class UsuarioQueries:
    @strawberry.field(
        description=(
            "La ficha de alguien que trabaja en la empresa activa. Para la "
            "lista completa use `miembros`."
        )
    )
    @requiere_permiso
    @auto_permisos(recurso="SEGU_USUARIOS", operacion="ver")
    def usuario(self, info: strawberry.Info, id: strawberry.ID) -> UsuarioType | None:
        try:
            fila = membresias.persona_de_la_empresa(int(id))
        except ValidationError as error:
            raise GraphQLError("; ".join(error.messages)) from error
        return UsuarioType.desde_modelo(fila)


@strawberry.type
class UsuarioQuery(UsuarioQueries):
    pass
