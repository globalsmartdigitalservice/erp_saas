"""Las mutations del login."""

import strawberry
from django.conf import settings
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from comun.membresias.graphql.types import EmpresaDelUsuarioType
from comun.usuarios.graphql.types import UsuarioType
from dominios.seguridad.services import login as svc


def _traducir(error: ValidationError) -> GraphQLError:
    """El `code` de Django sube a `extensions` para que el cliente decida sin
    leer el texto: comparar mensajes se rompe al reescribir una palabra, y se
    rompe en silencio."""
    codigo = getattr(error, "code", None)
    extensions = {"code": codigo} if codigo else None
    return GraphQLError("; ".join(error.messages), extensions=extensions)


def _poner_cookies(info, ingreso) -> None:
    """Escribe las dos cookies.

     `path` distinto a propósito: el refresh solo se manda a la ruta que lo
    renueva, así el token de 7 días no viaja en cada petición. Hoy los dos
    coinciden porque el endpoint es uno solo."""
    respuesta = info.context.response
    comunes = {
        "httponly": settings.COOKIE_HTTPONLY,
        "samesite": settings.COOKIE_SAMESITE,
        "secure": settings.COOKIE_SECURE,
    }
    respuesta.set_cookie(
        settings.COOKIE_ACCESO,
        ingreso.acceso,
        max_age=int(settings.JWT_VIDA_ACCESO.total_seconds()),
        **comunes,
    )
    respuesta.set_cookie(
        settings.COOKIE_REFRESH,
        ingreso.refresh,
        max_age=int(settings.JWT_VIDA_REFRESH.total_seconds()),
        **comunes,
    )


def _borrar_cookies(info) -> None:
    respuesta = info.context.response
    respuesta.delete_cookie(settings.COOKIE_ACCESO)
    respuesta.delete_cookie(settings.COOKIE_REFRESH)


@strawberry.type(name="ResultadoIngreso")
class ResultadoIngresoType:
    """No trae los tokens: van en cookies `HttpOnly`.

    `necesitaElegirEmpresa` en true significa que trabaja en más de una y
    todavía no eligió: no hay sesión abierta y `empresas` trae las opciones."""

    necesita_elegir_empresa: bool
    usuario: UsuarioType | None
    empresas: list[EmpresaDelUsuarioType]

    @classmethod
    def desde_ingreso(cls, ingreso) -> "ResultadoIngresoType":
        return cls(
            necesita_elegir_empresa=ingreso.necesita_elegir_empresa,
            usuario=UsuarioType.desde_modelo(ingreso.usuario),
            empresas=[
                EmpresaDelUsuarioType.desde_modelo(m) for m in ingreso.empresas
            ],
        )


@strawberry.input(name="IngresarInput")
class IngresarInput:
    """`identificador` es el nombre de usuario o el correo. `mac` la manda
    el cliente instalado; sin ella no se comprueba el equipo."""

    identificador: str
    password: str
    empresa_id: strawberry.ID | None = None
    mac: str | None = None


@strawberry.type
class LoginMutations:
    @strawberry.mutation(
        description=(
            "Entrar. Con una sola empresa entra directo; con varias devuelve "
            "la lista y NO abre sesión hasta que se elija. Los tokens van en "
            "cookies HttpOnly, no en la respuesta."
        )
    )
    def ingresar(
        self, info: strawberry.Info, datos: IngresarInput
    ) -> ResultadoIngresoType:
        try:
            ingreso = svc.ingresar(
                identificador=datos.identificador,
                password=datos.password,
                empresa_id=(
                    int(datos.empresa_id) if datos.empresa_id is not None else None
                ),
                request=info.context.request,
                mac=datos.mac,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        if not ingreso.necesita_elegir_empresa:
            _poner_cookies(info, ingreso)
        return ResultadoIngresoType.desde_ingreso(ingreso)

    @strawberry.mutation(
        description=(
            "El segundo paso cuando había varias empresas. Se piden las "
            "credenciales otra vez: hasta acá no se emitió ningún token, así "
            "que no hay nada que demuestre quién es."
        )
    )
    def elegir_empresa(
        self,
        info: strawberry.Info,
        datos: IngresarInput,
        empresa_id: strawberry.ID,
    ) -> ResultadoIngresoType:
        try:
            ingreso = svc.elegir_empresa(
                identificador=datos.identificador,
                password=datos.password,
                empresa_id=int(empresa_id),
                request=info.context.request,
                mac=datos.mac,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        _poner_cookies(info, ingreso)
        return ResultadoIngresoType.desde_ingreso(ingreso)

    @strawberry.mutation(
        description=(
            "Renueva la sesión con el refresh de la cookie. Cada uso emite "
            "uno nuevo y el anterior deja de servir."
        )
    )
    def renovar_sesion(self, info: strawberry.Info) -> ResultadoIngresoType:
        crudo = info.context.request.COOKIES.get(settings.COOKIE_REFRESH)
        if not crudo:
            raise GraphQLError(
                svc.SESION_MUERTA,
                extensions={"code": svc.CODIGO_SESION_MUERTA},
            )

        try:
            ingreso = svc.renovar(refresh=crudo)
        except ValidationError as error:
            # Se borran las cookies: si el refresh ya no sirve, dejarlas
            # puestas hace que el frontend reintente en loop.
            _borrar_cookies(info)
            raise _traducir(error) from error

        _poner_cookies(info, ingreso)
        return ResultadoIngresoType.desde_ingreso(ingreso)

    @strawberry.mutation(
        description=(
            "Cerrar sesión. Corta la renovación en el acto; el token de "
            "acceso que ya está emitido sigue valiendo hasta 15 minutos."
        )
    )
    def salir(self, info: strawberry.Info) -> bool:
        crudo = info.context.request.COOKIES.get(settings.COOKIE_ACCESO)
        _borrar_cookies(info)

        if not crudo:
            # Ya estaba afuera. No es un error: apretar "salir" dos veces
            # tiene que ser inofensivo.
            return True

        from dominios.seguridad import tokens

        try:
            datos = tokens.leer(crudo, tipo=tokens.TIPO_ACCESO)
        except tokens.TokenInvalido:
            return True

        svc.salir(sesion_id=datos["ses"])
        return True


@strawberry.type
class LoginMutation(LoginMutations):
    pass
