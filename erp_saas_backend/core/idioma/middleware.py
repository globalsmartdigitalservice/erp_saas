"""Middleware que pone el idioma activo en el contexto.

 PROVISIONAL — lee el idioma de una CABECERA HTTP, igual que el de
empresa, y por el mismo motivo: sin login no se puede probar el
multiidioma de punta a punta.

    curl -H "X-Empresa-Id: 7" -H "X-Idioma: 2" http://localhost:10000/graphql/

Está apagado por defecto (`TENANCY_POR_CABECERA = False`) y encendido en
`local`. Comparte el flag con el de empresa a propósito: son la misma
muleta y se van juntos el día del login, cuando el idioma pase a salir de
la preferencia del usuario.

 UNA CABECERA VACÍA O ROTA NO ES ERROR, al revés que `X-Empresa-Id`, que
devuelve 400 si no es un número. Sin empresa no se puede responder sin
arriesgar una fuga; sin idioma sí, se muestran los textos como están
guardados. Quien manda basura en la cabecera ve todo en español, no una
pantalla de error.
"""

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

from .contexto import establecer_idioma, restaurar_idioma

CABECERA = "HTTP_X_IDIOMA"


class IdiomaDesdeCabeceraMiddleware:
    def __init__(self, get_response):
        if not getattr(settings, "TENANCY_POR_CABECERA", False):
            raise MiddlewareNotUsed

        self.get_response = get_response

    def __call__(self, request):
        crudo = request.META.get(CABECERA)

        try:
            idioma_id = int(crudo)
        except (TypeError, ValueError):
           
            return self.get_response(request)

        token = establecer_idioma(idioma_id)
        try:
            return self.get_response(request)
        finally:
          
            restaurar_idioma(token)
