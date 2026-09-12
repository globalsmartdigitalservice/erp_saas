"""Las consultas de usuarios."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from comun.usuarios import api as usuarios
from dominios.seguridad.permisos_graphql import requiere_autenticacion

from .types import UsuarioType


@strawberry.type
class UsuarioQueries:
    @strawberry.field(
        description=(
            "Un usuario de SU cliente, por id. Para ver los de una empresa "
            "use `miembros`, que filtra."
        )
    )
    @requiere_autenticacion
    def usuario(self, info: strawberry.Info, id: strawberry.ID) -> UsuarioType | None:
        
        try:
            fila = usuarios.obtener_usuario_del_cliente(int(id))
        except ValidationError as error:
            raise GraphQLError("; ".join(error.messages)) from error
        return UsuarioType.desde_modelo(fila)


@strawberry.type
class UsuarioQuery(UsuarioQueries):
    pass
