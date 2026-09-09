"""Las consultas de membresías."""

import strawberry

from comun.membresias import api as membresias
from comun.usuarios import api as usuarios
from comun.usuarios.graphql.types import UsuarioType

from .types import EmpresaDelUsuarioType, MembresiaType


@strawberry.type
class MembresiaQueries:
    @strawberry.field(
        description=(
            "En qué empresas está dada de alta una persona. Es lo que llena "
            "el selector '¿dónde desea trabajar?' del login, y corre ANTES "
            "de elegir empresa."
        )
    )
    def empresas_del_usuario(
        self, usuario_id: strawberry.ID
    ) -> list[EmpresaDelUsuarioType]:
        return [
            EmpresaDelUsuarioType.desde_modelo(m)
            for m in membresias.empresas_de(int(usuario_id))
        ]

    @strawberry.field(
        description=(
            "Quiénes trabajan en la empresa activa. Es la lista de usuarios "
            "de la empresa; NO devuelve gente de otros clientes."
        )
    )
    def miembros(self, estado_id: strawberry.ID | None = None) -> list[MembresiaType]:
        filas = membresias.listar_membresias(
            int(estado_id) if estado_id is not None else None
        )
        # El batch a mano del que depende no tener N+1: se juntan todos
        # los `usuario_id` y se piden en una sola consulta. El
        # proyecto no usa DataLoader.
        personas = usuarios.obtener_usuarios({f.usuario_id for f in filas})
        resueltas = {
            id_: UsuarioType.desde_modelo(u) for id_, u in personas.items()
        }
        return [
            MembresiaType.desde_modelo(f, resueltas.get(f.usuario_id)) for f in filas
        ]

    @strawberry.field(description="La membresía de una persona en la empresa activa.")
    def membresia(self, usuario_id: strawberry.ID) -> MembresiaType | None:
        fila = membresias.membresia_de(int(usuario_id))
        if fila is None:
            return None
        persona = usuarios.obtener_usuario(fila.usuario_id)
        return MembresiaType.desde_modelo(
            fila, UsuarioType.desde_modelo(persona) if persona else None
        )


@strawberry.type
class MembresiaQuery(MembresiaQueries):
    pass
