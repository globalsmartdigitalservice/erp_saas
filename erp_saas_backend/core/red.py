

from django.conf import settings


def ip_del_cliente(request) -> str | None:
    """
    La IP real de quien hace la petición.

    Lee `X-Forwarded-For` **desde la derecha**, salteando
    `settings.PROXIES_CONFIABLES` entradas. Con 0, lo ignora.
    """
    if request is None:
        return None

    proxies = getattr(settings, "PROXIES_CONFIABLES", 0)
    remota = request.META.get("REMOTE_ADDR")

    if proxies <= 0:
       
        return remota

    reenviadas = request.META.get("HTTP_X_FORWARDED_FOR", "")
    cadena = [p.strip() for p in reenviadas.split(",") if p.strip()]
    if not cadena:
        return remota

    indice = len(cadena) - proxies
    if indice < 0:
   
        return remota

    return cadena[indice]


def user_agent_de(request) -> str:
    """El navegador o cliente, recortado a lo que entra en la columna."""
    if request is None:
        return ""
    return (request.META.get("HTTP_USER_AGENT") or "")[:400]


__all__ = ["ip_del_cliente", "user_agent_de"]
