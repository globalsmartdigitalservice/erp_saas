"""Las mutations de membresías."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import requiere_permiso

from comun.membresias import api as membresias
from comun.usuarios import api as usuarios
from comun.usuarios.graphql.types import UsuarioType

from .inputs import AfiliarInput, DesafiliarInput
from .types import MembresiaType


def _traducir(error: ValidationError) -> GraphQLError:
    return GraphQLError("; ".join(error.messages))


def _a_membresia(fila) -> MembresiaType:
    persona = usuarios.obtener_usuario(fila.usuario_id)
    return MembresiaType.desde_modelo(
        fila, UsuarioType.desde_modelo(persona) if persona else None
    )


@auto_permisos(recurso="SEGU_MIEMBROS")
@strawberry.type
class MembresiaMutations:
    @strawberry.mutation(
        description="Da de alta a una persona en la empresa de la sesión."
    )
    @requiere_permiso
    def afiliar(self, info: strawberry.Info, datos: AfiliarInput) -> MembresiaType:
        try:
            fila = membresias.afiliar(
                usuario_id=int(datos.usuario_id),
                estado_id=int(datos.estado_id),
                fecha_asignacion=datos.fecha_asignacion,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_membresia(fila)

    @strawberry.mutation(
        description=(
            "Da de alta a una persona en la empresa de la sesión Y EN "
            "TODAS SUS SUCURSALES. Es el 'dar de alta en todo el grupo' "
            "para el gerente de una cadena. Devuelve solo las creadas: donde ya "
            "estaba, se saltea sin dar error."
        )
    )
    @requiere_permiso
    def afiliar_al_grupo(self, info: strawberry.Info, datos: AfiliarInput) -> list[MembresiaType]:
        try:
            filas = membresias.afiliar_al_grupo(
                usuario_id=int(datos.usuario_id),
                estado_id=int(datos.estado_id),
                fecha_asignacion=datos.fecha_asignacion,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        persona = usuarios.obtener_usuario(int(datos.usuario_id))
        resuelta = UsuarioType.desde_modelo(persona) if persona else None
        return [MembresiaType.desde_modelo(f, resuelta) for f in filas]

    @strawberry.mutation(
        description=(
            "Saca a una persona de esta empresa. NO borra la fila ni la toca "
            "en las otras empresas donde trabaje."
        )
    )
    @requiere_permiso
    def desafiliar(self, info: strawberry.Info, datos: DesafiliarInput) -> MembresiaType:
        try:
            fila = membresias.desafiliar(
                membresia_id=int(datos.membresia_id),
                estado_baja_id=int(datos.estado_baja_id),
                fecha_finalizacion=datos.fecha_finalizacion,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_membresia(fila)

    @strawberry.mutation(
        description=(
            "El que se fue y volvió: reactiva su fila en vez de crear otra, "
            "así el historial queda en un solo lugar."
        )
    )
    @requiere_permiso
    def reactivar_membresia(
        self,
        info: strawberry.Info, membresia_id: strawberry.ID, estado_activo_id: strawberry.ID
    ) -> MembresiaType:
        try:
            fila = membresias.reactivar(
                membresia_id=int(membresia_id),
                estado_activo_id=int(estado_activo_id),
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_membresia(fila)


@strawberry.type
class MembresiaMutation(MembresiaMutations):
    pass
