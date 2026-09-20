"""Las mutations de los procesos que cruzan varias familias.

Viven acá y no en la app de cada uno porque ningún dominio importa
`procesos/`: la dependencia va en un solo sentido.
"""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from comun.membresias import api as membresias
from comun.membresias.graphql.inputs import DesafiliarInput
from comun.membresias.graphql.types import MembresiaType
from comun.usuarios import api as usuarios
from comun.usuarios.graphql.types import UsuarioType
from core.tenancy import empresa as contexto_empresa
from dominios.seguridad.permisos import auto_permisos, codename_de
from dominios.seguridad.permisos_graphql import (
    exigir_permiso,
    requiere_autenticacion,
    requiere_permiso,
    usuario_de_la_sesion,
)
from procesos import (
    administrar_miembros,
    alta_de_miembro,
    cambio_de_password,
    reseteo_de_password,
)

from .inputs import (
    CambiarMiPasswordInput,
    DarDeAltaMiembroInput,
    ResetearPasswordInput,
)
from .types import AltaDeMiembroType

PERMISO_ASIGNAR_ROL = codename_de("SEGU_ROLES", "asignar_rol")
PERMISO_DESACTIVAR = codename_de("SEGU_USUARIOS", "desactivar_usuario")
PERMISO_REACTIVAR = codename_de("SEGU_USUARIOS", "reactivar_usuario")


def _traducir(error: ValidationError) -> GraphQLError:
    return GraphQLError("; ".join(error.messages))


def _exigir_en_sus_empresas(info, usuario_id: int, codigo: str) -> None:
    for membresia in administrar_miembros.membresias_vigentes_de(usuario_id):
        with contexto_empresa(membresia.empresa_id):
            exigir_permiso(info, codigo)


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
    @requiere_autenticacion
    @requiere_permiso("segu_miembros_resetear_password")
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
    @requiere_autenticacion
    @requiere_permiso("segu_miembros_dar_de_alta_miembro")
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


@auto_permisos(recurso="SEGU_USUARIOS")
@strawberry.type
class CuentaMutations:
    @strawberry.mutation(
        description=(
            "Apaga la cuenta: la persona no entra a ninguna empresa. Exige el "
            "permiso en cada empresa donde trabaja y rechaza si deja a alguna "
            "sin quien la administre. Para sacarla de una sola, use `desafiliar`."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_usuarios_desactivar_usuario")
    def desactivar_usuario(self, info: strawberry.Info, id: strawberry.ID) -> UsuarioType:
        try:
            persona = membresias.persona_de_la_empresa(int(id))
            _exigir_en_sus_empresas(info, persona.pk, PERMISO_DESACTIVAR)
            cuenta = administrar_miembros.desactivar_cuenta(persona.pk)
        except ValidationError as error:
            raise _traducir(error) from error
        return UsuarioType.desde_modelo(cuenta)

    @strawberry.mutation(
        description=(
            "Vuelve a habilitar la cuenta. Exige el permiso en cada empresa "
            "donde la persona trabaja."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_usuarios_reactivar_usuario")
    def reactivar_usuario(self, info: strawberry.Info, id: strawberry.ID) -> UsuarioType:
        try:
            persona = membresias.persona_de_la_empresa(int(id))
            _exigir_en_sus_empresas(info, persona.pk, PERMISO_REACTIVAR)
            cuenta = usuarios.reactivar_usuario(persona.pk)
        except ValidationError as error:
            raise _traducir(error) from error
        return UsuarioType.desde_modelo(cuenta)


@auto_permisos(recurso="SEGU_MIEMBROS")
@strawberry.type
class BajaDeMiembroMutations:
    @strawberry.mutation(
        description=(
            "Saca a una persona de esta empresa: no borra la fila ni toca sus "
            "otras empresas. Rechaza si es la última que puede administrarla."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_miembros_desafiliar")
    def desafiliar(self, info: strawberry.Info, datos: DesafiliarInput) -> MembresiaType:
        try:
            fila = administrar_miembros.desafiliar(
                membresia_id=int(datos.membresia_id),
                estado_baja_id=int(datos.estado_baja_id),
                fecha_finalizacion=datos.fecha_finalizacion,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        persona = usuarios.obtener_usuario(fila.usuario_id)
        return MembresiaType.desde_modelo(
            fila, UsuarioType.desde_modelo(persona) if persona else None
        )


@strawberry.type
class ProcesosMutation(
    CambioDePasswordMutations,
    ReseteoDePasswordMutations,
    AltaDeMiembroMutations,
    CuentaMutations,
    BajaDeMiembroMutations,
):
    pass
