"""Las consultas de membresías."""

import strawberry

from comun.membresias import api as membresias
from comun.usuarios import api as usuarios
from comun.usuarios.graphql.types import UsuarioType

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import requiere_permiso

from .types import MembresiaType, PersonaEncontradaType


@auto_permisos(recurso="SEGU_MIEMBROS")
@strawberry.type
class MembresiaQueries:
    @strawberry.field(description="La membresía de una persona en la empresa activa.")
    @requiere_permiso
    @auto_permisos(recurso="SEGU_MIEMBROS", operacion="ver")
    def membresia(
        self, info: strawberry.Info, usuario_id: strawberry.ID
    ) -> MembresiaType | None:
        fila = membresias.membresia_de(int(usuario_id))
        if fila is None:
            return None
        persona = usuarios.obtener_usuario(fila.usuario_id)
        return MembresiaType.desde_modelo(
            fila, UsuarioType.desde_modelo(persona) if persona else None
        )

    @strawberry.field(
        description=(
            "Una persona del cliente por su correo exacto, para darla de alta "
            "acá sin crearla de nuevo. Devuelve lo mínimo, y null si no es del "
            "cliente."
        )
    )
    @requiere_permiso
    @auto_permisos(recurso="SEGU_MIEMBROS", operacion="buscar_por_correo")
    def persona_por_correo(
        self, info: strawberry.Info, email: str
    ) -> PersonaEncontradaType | None:
        persona = usuarios.buscar_por_email(email)
        if persona is None:
            return None
        return PersonaEncontradaType.desde_modelo(
            persona, trabaja_aca=membresias.membresia_de(persona.pk) is not None
        )


@strawberry.type
class MembresiaQuery(MembresiaQueries):
    pass
