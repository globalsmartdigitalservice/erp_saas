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


def _poner_cookies(info, resultado) -> None:
    """Escribe las dos cookies.

     `path` distinto a propósito: el refresh solo se manda a la ruta que lo
    renueva, así el token de 7 días no viaja en cada petición. Hoy los dos
    coinciden porque el endpoint es uno solo."""
    response = info.context.response
    comunes = {
        "httponly": settings.COOKIE_HTTPONLY,
        "samesite": settings.COOKIE_SAMESITE,
        "secure": settings.COOKIE_SECURE,
    }
    response.set_cookie(
        settings.COOKIE_ACCESO,
        resultado.acceso,
        max_age=int(settings.JWT_VIDA_ACCESO.total_seconds()),
        **comunes,
    )
    response.set_cookie(
        settings.COOKIE_REFRESH,
        resultado.refresh,
        max_age=int(settings.JWT_VIDA_REFRESH.total_seconds()),
        **comunes,
    )


def _borrar_cookies(info) -> None:
    response = info.context.response
    response.delete_cookie(settings.COOKIE_ACCESO)
    response.delete_cookie(settings.COOKIE_REFRESH)


@strawberry.type(name="ResultadoLogin")
class ResultadoLoginType:
    """No trae los tokens: van en cookies `HttpOnly`.

    `necesitaElegirEmpresa` en true significa que trabaja en más de una y
    todavía no eligió: no hay sesión abierta, `empresas` trae las opciones y
    `usuario` viene vacío."""

    necesita_elegir_empresa: bool
    usuario: UsuarioType | None
    empresas: list[EmpresaDelUsuarioType]

    @classmethod
    def desde_resultado(cls, resultado) -> "ResultadoLoginType":
        return cls(
            necesita_elegir_empresa=resultado.necesita_elegir_empresa,
            usuario=cls._ficha(resultado),
            empresas=[
                EmpresaDelUsuarioType.desde_modelo(m) for m in resultado.empresas
            ],
        )

    @staticmethod
    def _ficha(resultado) -> UsuarioType | None:
        """Mientras falte elegir empresa no se devuelve la ficha: con dos
        cuentas del mismo correo, cualquiera de las dos sería arbitraria."""
        if resultado.necesita_elegir_empresa:
            return None
        return UsuarioType.desde_modelo(resultado.usuario)


@strawberry.input(name="LoginInput")
class LoginInput:
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
    def login(
        self, info: strawberry.Info, datos: LoginInput
    ) -> ResultadoLoginType:
        try:
            resultado = svc.login(
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

        if not resultado.necesita_elegir_empresa:
            _poner_cookies(info, resultado)
        return ResultadoLoginType.desde_resultado(resultado)

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
        datos: LoginInput,
        empresa_id: strawberry.ID,
    ) -> ResultadoLoginType:
        try:
            resultado = svc.elegir_empresa(
                identificador=datos.identificador,
                password=datos.password,
                empresa_id=int(empresa_id),
                request=info.context.request,
                mac=datos.mac,
            )
        except ValidationError as error:
            raise _traducir(error) from error

        _poner_cookies(info, resultado)
        return ResultadoLoginType.desde_resultado(resultado)

    @strawberry.mutation(
        description=(
            "Renueva la sesión con el refresh de la cookie. Cada uso emite "
            "uno nuevo y el anterior deja de servir."
        )
    )
    def refresh_session(self, info: strawberry.Info) -> ResultadoLoginType:
        crudo = info.context.request.COOKIES.get(settings.COOKIE_REFRESH)
        if not crudo:
            raise GraphQLError(
                svc.SESION_MUERTA,
                extensions={"code": svc.CODIGO_SESION_MUERTA},
            )

        try:
            resultado = svc.refresh(token=crudo)
        except ValidationError as error:
            # Se borran las cookies: si el refresh ya no sirve, dejarlas
            # puestas hace que el frontend reintente en loop.
            _borrar_cookies(info)
            raise _traducir(error) from error

        _poner_cookies(info, resultado)
        return ResultadoLoginType.desde_resultado(resultado)

    @strawberry.mutation(
        description=(
            "Cerrar sesión. Corta la renovación en el acto; el token de "
            "acceso que ya está emitido sigue valiendo hasta 15 minutos."
        )
    )
    def logout(self, info: strawberry.Info) -> bool:
        crudo = info.context.request.COOKIES.get(settings.COOKIE_ACCESO)
        _borrar_cookies(info)

        if not crudo:
            # Ya estaba afuera. No es un error: apretar "salir" dos veces
            # tiene que ser inofensivo.
            return True

        from dominios.seguridad import tokens

        try:
            datos = tokens.leer(crudo, tipo=tokens.TIPO_ACCESO)
        except tokens.InvalidTokenError:
            return True

        svc.logout(sesion_id=datos["ses"])
        return True


@strawberry.type
class LoginMutation(LoginMutations):
    pass
