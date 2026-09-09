"""Las consultas de usuarios."""

import strawberry

from comun.usuarios import api as usuarios

from .types import UsuarioType


@strawberry.type
class UsuarioQueries:
    @strawberry.field(
        description=(
            "Un usuario por su id. Para ver los de una empresa usá "
            "`miembros`, que filtra."
        )
    )
    def usuario(self, id: strawberry.ID) -> UsuarioType | None:
        fila = usuarios.obtener_usuario(int(id))
        return UsuarioType.desde_modelo(fila) if fila else None


@strawberry.type
class UsuarioQuery(UsuarioQueries):
    pass
