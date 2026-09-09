"""Las mutations de usuarios."""

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import requiere_permiso

from comun.usuarios import api as usuarios

from .inputs import ActualizarUsuarioInput, CambiarPasswordInput, CrearUsuarioInput
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
    @strawberry.mutation(
        description=(
            "Da de alta a una persona en el SISTEMA. No la mete en ninguna "
            "empresa: para eso está `afiliar`. Arranca obligada a cambiar la "
            "contraseña en el primer ingreso."
        )
    )
    @requiere_permiso
    def crear_usuario(self, info: strawberry.Info, datos: CrearUsuarioInput) -> UsuarioType:
        try:
            fila = usuarios.crear_usuario(
                username=datos.username,
                email=datos.email,
                password=datos.password,
                first_name=datos.first_name,
                last_name=datos.last_name,
                seg_apellido=datos.seg_apellido,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return UsuarioType.desde_modelo(fila)

    @strawberry.mutation(description="Los datos personales. La contraseña no.")
    @requiere_permiso
    def actualizar_usuario(
        self,
        info: strawberry.Info, id: strawberry.ID, datos: ActualizarUsuarioInput
    ) -> UsuarioType:
        try:
            fila = usuarios.actualizar_usuario(
                int(id),
                email=datos.email,
                first_name=datos.first_name,
                last_name=datos.last_name,
                seg_apellido=datos.seg_apellido,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return UsuarioType.desde_modelo(fila)

    @strawberry.mutation(
        description=(
            "La persona cambia SU PROPIA contraseña, sabiendo la anterior. "
            "Nadie más se la puede cambiar."
        )
    )
    @requiere_permiso
    def cambiar_password(
        self,
        info: strawberry.Info, id: strawberry.ID, datos: CambiarPasswordInput
    ) -> UsuarioType:
        try:
            fila = usuarios.cambiar_password(
                usuario_id=int(id),
                password_actual=datos.password_actual,
                password_nueva=datos.password_nueva,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return UsuarioType.desde_modelo(fila)

    @strawberry.mutation(
        description=(
            "Baja del sistema entero: no entra a ninguna empresa. Para "
            "sacarlo de UNA, usá `desafiliar`."
        )
    )
    @requiere_permiso
    def desactivar_usuario(self, info: strawberry.Info, id: strawberry.ID) -> UsuarioType:
        try:
            fila = usuarios.desactivar_usuario(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return UsuarioType.desde_modelo(fila)

    @strawberry.mutation(description="Vuelve a habilitar a una persona dada de baja.")
    @requiere_permiso
    def reactivar_usuario(self, info: strawberry.Info, id: strawberry.ID) -> UsuarioType:
        try:
            fila = usuarios.reactivar_usuario(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return UsuarioType.desde_modelo(fila)


@strawberry.type
class UsuarioMutation(UsuarioMutations):
    pass
