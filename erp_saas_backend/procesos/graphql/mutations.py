"""Las mutations de los procesos que cruzan varias familias.

Viven acá y no en la app de cada uno porque ningún dominio importa
`procesos/`: la dependencia va en un solo sentido.
"""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from comun.membresias.graphql.types import MembresiaType
from comun.usuarios.graphql.types import UsuarioType
from dominios.seguridad.permisos import auto_permisos, codename_de
from dominios.seguridad.permisos_graphql import (
    exigir_permiso,
    requiere_autenticacion,
    requiere_permiso,
    usuario_de_la_sesion,
)
from procesos import alta_de_miembro, cambio_de_password, reseteo_de_password

from .inputs import (
    CambiarMiPasswordInput,
    DarDeAltaMiembroInput,
    ResetearPasswordInput,
)
from .types import AltaDeMiembroType

PERMISO_ASIGNAR_ROL = codename_de("SEGU_ROLES", "asignar_rol")


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
        request = info.context.request
        try:
            cambio_de_password.cambiar(
                usuario_id=usuario_de_la_sesion(info).pk,
                sesion_id=getattr(request, "sesion_id", None),
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


@auto_permisos(recurso="SEGU_MIEMBROS")
@strawberry.type
class AltaDeMiembroMutations:
    @strawberry.mutation(
        description=(
            "Da de alta a una persona en la empresa activa: crea su cuenta si "
            "hace falta, la afilia y le asigna los roles, todo o nada. Con roles "
            "exige además el permiso de asignarlos."
        )
    )
    @requiere_permiso
    def dar_de_alta_miembro(
        self, info: strawberry.Info, datos: DarDeAltaMiembroInput
    ) -> AltaDeMiembroType:
        if datos.rol_ids:
            exigir_permiso(info, PERMISO_ASIGNAR_ROL)

        persona = None
        if datos.persona is not None:
            persona = alta_de_miembro.PersonaNueva(
                username=datos.persona.username,
                email=datos.persona.email,
                first_name=datos.persona.first_name,
                last_name=datos.persona.last_name,
                seg_apellido=datos.persona.seg_apellido,
                password=datos.persona.password,
            )

        try:
            alta = alta_de_miembro.dar_de_alta(
                usuario_id=int(datos.usuario_id) if datos.usuario_id is not None else None,
                persona=persona,
                rol_ids=[int(rol_id) for rol_id in datos.rol_ids],
                asignado_por_id=usuario_de_la_sesion(info).pk,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        return AltaDeMiembroType(
            membresia=MembresiaType.desde_modelo(
                alta.membresia, UsuarioType.desde_modelo(alta.usuario)
            ),
            password_temporal=alta.password_temporal,
        )


@strawberry.type
class ProcesosMutation(
    CambioDePasswordMutations, ReseteoDePasswordMutations, AltaDeMiembroMutations
):
    pass
