"""El middleware del login: lee el token de la cookie y arma la petición.

Hace dos cosas, una por request:

    request.user           ← quién es
    empresa_actual()       ← en qué empresa está parado
    idioma_actual()        ← en qué idioma quiere leer, si eligió uno

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

 DEJA `usuario_del_token` ADEMÁS DE `user`, y no es redundante: a `user` lo
puede haber puesto Django desde la cookie del `/admin/`, que no pasa por
ninguna de las comprobaciones de acá. Las guardas de GraphQL necesitan saber
cuál de los dos fue, y por eso existe esta marca. Ver `TRUST_DJANGO_SESSION`.

Y no se puede resolver poniendo `AnonymousUser` cuando no hay token: este
middleware corre para TODAS las peticiones, así que eso dejaría el `/admin/`
inutilizable.

 SE COMPRUEBA LA SESIÓN CONTRA LA BASE EN CADA PETICIÓN, y eso no es un
lujo: sin esto, dar de baja a alguien no lo saca del sistema. Su token ya
lleva la empresa adentro y la renovación tampoco mira la membresía, así
que se queda adentro mientras siga renovando. **No es una ventana de 15
minutos: es indefinida.**

Y no cuesta una consulta más. Antes se buscaba al usuario para mirarle
`is_active` —una consulta igual—; ahora se busca la sesión, que con un
`select_related` trae la membresía y la persona en la misma. Se paga lo
mismo y se contestan cuatro cosas en vez de una.
"""

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from core.idioma import establecer_idioma, restaurar_idioma
from core.tenancy import establecer_empresa, restaurar_empresa
from dominios.seguridad import tokens
from dominios.seguridad.services import login


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
         
            return self.get_response(request)

        membresia = self._membresia_vigente(datos)
        if membresia is None:
            
            return self.get_response(request)

        request.user = membresia.usuario
        request.usuario_del_token = membresia.usuario
        # La sesión ya está resuelta acá. Sin dejarla puesta, quien la
        # necesite tiene que volver a leer la cookie y decodificar el token.
        request.sesion_id = datos["ses"]

        marca = establecer_empresa(membresia.empresa_id)
        marca_idioma = (
            establecer_idioma(membresia.usuario.idioma_id)
            if membresia.usuario.idioma_id
            else None
        )
        try:
            return self.get_response(request)
        finally:
            if marca_idioma is not None:
                restaurar_idioma(marca_idioma)
            restaurar_empresa(marca)

    def _leer_token(self, request) -> dict | None:
        crudo = request.COOKIES.get(settings.COOKIE_ACCESO)
        if not crudo:
            return None
        try:
            return tokens.leer(crudo, tipo=tokens.TIPO_ACCESO)
        except tokens.InvalidTokenError:
        
            return None

    def _membresia_vigente(self, datos):
        sesion = login.sesion_vigente(datos)
        return sesion.usuario_empresa if sesion else None


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
