

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import JsonResponse

from .contexto import establecer_empresa, restaurar_empresa

CABECERA = "HTTP_X_EMPRESA_ID"


class EmpresaDesdeCabeceraMiddleware:
    def __init__(self, get_response):
        if not getattr(settings, "TENANCY_POR_CABECERA", False):
            # Django saca el middleware de la cadena y ni siquiera lo
            # llama. Es el mecanismo estándar para middlewares que solo
            # aplican en algunos entornos.
            raise MiddlewareNotUsed

        self.get_response = get_response

    def __call__(self, request):
        crudo = request.META.get(CABECERA)

        # Sin cabecera no se inventa nada: se sigue sin empresa. Los
        # managers ya saben qué hacer con eso (Tipologia muestra las del
        # sistema, ModeloTenant revienta).
        if not crudo:
            return self.get_response(request)

        try:
            empresa_id = int(crudo)
        except (TypeError, ValueError):
            return JsonResponse(
                {"error": f"La cabecera X-Empresa-Id tiene que ser un número, llegó '{crudo}'."},
                status=400,
            )

        token = establecer_empresa(empresa_id)
        try:
            return self.get_response(request)
        finally:
            restaurar_empresa(token)
