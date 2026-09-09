"""El middleware del login: lee el token de la cookie y arma la petición.

Hace dos cosas, una por request:

    request.user           ← quién es
    empresa_actual()       ← en qué empresa está parado

Reemplaza al provisional de `core/tenancy/middleware.py`, que leía la
empresa de una cabecera HTTP porque todavía no había login. Cambió una
línea: en vez de la cabecera se lee el claim `empresa_id` del token ya
verificado; fijar el contexto y restaurarlo al terminar quedó igual.

 LA EMPRESA VIAJA DENTRO DEL TOKEN Y NO COMO PARÁMETRO porque el token
está firmado y un parámetro no. Si viniera en la petición, cualquiera
cambiaría el número y leería los datos de otro cliente. Por eso **cambiar
de empresa exige un token nuevo**.

 SE RESTAURA EN UN `finally` porque el servidor es ASGI y un mismo hilo
atiende varias requests: sin restaurar, la empresa de un usuario se le
queda pegada a la siguiente petición.

 NO RECHAZA LA PETICIÓN SI NO HAY TOKEN. Sigue de largo sin usuario y
sin empresa: quién puede hacer qué lo deciden los resolvers y `has_perm()`,
y un middleware que devuelve 401 a todo dejaría afuera al propio login.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from core.tenancy import establecer_empresa, restaurar_empresa
from dominios.seguridad import tokens

UserModel = get_user_model()


class SesionPorTokenMiddleware:
    """
    Va DESPUÉS de `AuthenticationMiddleware` de Django y lo pisa: aquel
    resuelve el usuario desde la cookie de sesión, que acá no se usa.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        datos = self._leer_token(request)

        if datos is None:
            # Sin token: petición anónima. El login entra por acá.
            return self.get_response(request)

        usuario = self._resolver_usuario(datos)
        if usuario is None:
            # Token válido pero el usuario ya no existe o está dado de
            # baja. Se sigue como anónimo en vez de reventar: dar de baja
            # a alguien no tiene que devolverle un error 500.
            return self.get_response(request)

        request.user = usuario

        marca = establecer_empresa(datos["emp"])
        try:
            return self.get_response(request)
        finally:
            restaurar_empresa(marca)

    def _leer_token(self, request) -> dict | None:
        crudo = request.COOKIES.get(settings.COOKIE_ACCESO)
        if not crudo:
            return None
        try:
            return tokens.leer(crudo, tipo=tokens.TIPO_ACCESO)
        except tokens.TokenInvalido:
            # Vencido, mal firmado o del tipo equivocado. Se ignora: el
            # cliente va a pedir uno nuevo con su refresh.
            return None

    def _resolver_usuario(self, datos):
        usuario = UserModel.objects.filter(pk=int(datos["sub"])).first()
        if usuario is None or not usuario.is_active:
            return None
        return usuario


class AnonimoPorDefectoMiddleware:
    """Deja `request.user` en `AnonymousUser` cuando no hay nada más.

    Existe para poder sacar el `AuthenticationMiddleware` de Django: sin él,
    `request.user` no existiría y cualquier código que lo lea fallaría con
    `AttributeError`. Hoy no está enchufado."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, "user"):
            request.user = AnonymousUser()
        return self.get_response(request)


__all__ = ["SesionPorTokenMiddleware", "AnonimoPorDefectoMiddleware"]
