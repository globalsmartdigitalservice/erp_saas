"""Los decoradores que PROTEGEN una mutation.

    @auto_permisos(recurso="CORE_MONEDAS")   ← solo CREA los permisos.
                                               NO protege nada.
    @requiere_autenticacion                  ← exige estar logueado
    @requiere_permiso                        ← exige además el permiso
    @solo_proveedor                          ← exige ser del proveedor

 Una mutation sin estos decoradores NO está protegida, y es deliberado:
el dev construye y los pone al final.

 EL ORDEN IMPORTA: `@strawberry.mutation` va siempre arriba de todo. Si
quedara debajo, Strawberry registraría la función SIN envolver y los guards
no correrían, sin dar ningún error.

 El permiso se DEDUCE, no se escribe a mano: con el literal, un código
mal tipeado no falla, simplemente no pasa nadie nunca, y se descubre en
producción.

 `usuario_de_la_sesion` contesta lo mismo que ellos para quien necesite
FIRMAR una fila: el autor sale de ahí, nunca del input."""

import functools

import strawberry
from django.conf import settings
from graphql import GraphQLError

from dominios.seguridad.permisos import METADATA, codename_de


SIN_PERMISO = "No tiene permiso para realizar esta acción."
SIN_SESION = "Debe iniciar sesión."


CODIGO_SIN_PERMISO = "FORBIDDEN"
CODIGO_SIN_SESION = "UNAUTHENTICATED"


APP_DE_LOS_PERMISOS = "seguridad"


def _info_de(args, kwargs):
    """El `info` de Strawberry, venga como venga: puede llegar por nombre o
    por posición según cómo esté escrito el resolver."""
    info = kwargs.get("info")
    if info is not None:
        return info
    for arg in args:
        if isinstance(arg, strawberry.Info):
            return arg
    return None


def usuario_de_la_sesion(info):
    """Quién llama. Ver `usuario_de_request`."""
    return usuario_de_request(getattr(info.context, "request", None))


def usuario_de_request(request):
    """Quién llama, y POR QUÉ PUERTA entró.

    `request.user` lo puede haber puesto el middleware del ERP desde el token,
    o Django desde la cookie del `/admin/`. La segunda no registra la sesión,
    no comprueba horario ni equipo, no la corta `desafiliar`, y por ella el
    superusuario pasa por encima de todos los permisos.

    Por eso solo se acepta la marca que deja el middleware del ERP. A la cookie
    de Django se le cree únicamente si `TRUST_DJANGO_SESSION` lo habilita, que
    en producción es `False` y en desarrollo `True` — ahí sirve para probar
    desde GraphiQL sin montar un login."""
    if request is None:
        return None

    usuario = getattr(request, "usuario_del_token", None)
    if usuario is not None:
        return usuario

    if settings.TRUST_DJANGO_SESSION:
        return getattr(request, "user", None)

    return None


def _exigir_sesion(args, kwargs, func):
    """El `info` y el usuario, o el error correspondiente."""
    info = _info_de(args, kwargs)
    if info is None:
        raise GraphQLError(
            f"'{func.__name__}' está protegido pero no recibe `info`. "
            f"Agregue el parámetro `info: strawberry.Info`: de ahí sale "
            f"quién está llamando."
        )

    usuario = usuario_de_la_sesion(info)
    if usuario is None or not usuario.is_authenticated:
        raise GraphQLError(SIN_SESION, extensions={"code": CODIGO_SIN_SESION})

    return usuario


def exigir_permiso(info, codigo: str) -> None:
    """Lo que hace `@requiere_permiso`, para cuando el permiso depende de lo que se pidió."""
    usuario = usuario_de_la_sesion(info)
    if usuario is None or not usuario.is_authenticated:
        raise GraphQLError(SIN_SESION, extensions={"code": CODIGO_SIN_SESION})
    _exigir_codigo(usuario, codigo)


def _exigir_codigo(usuario, codigo: str) -> None:
    if usuario.is_superuser:
        return
    if not usuario.has_perm(f"{APP_DE_LOS_PERMISOS}.{codigo}"):
        raise GraphQLError(SIN_PERMISO, extensions={"code": CODIGO_SIN_PERMISO})


def requiere_autenticacion(func):
    """Exige una sesión abierta. Nada más."""

    @functools.wraps(func)
    def guard(*args, **kwargs):
        _exigir_sesion(args, kwargs, func)
        return func(*args, **kwargs)

    guard._requiere_autenticacion = True
    return guard


def requiere_permiso(codigo=None):
    """Exige el permiso. Sin argumento, lo deduce de `@auto_permisos`.

        @requiere_permiso                 → core_monedas_crear_moneda
        @requiere_permiso("otro_codigo")  → ese, tal cual

    También exige estar logueado, así que `@requiere_autenticacion` sobra."""
   
    if callable(codigo):
        return _armar_guard(codigo, None)

    def decorador(func):
        return _armar_guard(func, codigo)

    return decorador


def _armar_guard(func, codigo_fijo):
    @functools.wraps(func)
    def guard(*args, **kwargs):
        usuario = _exigir_sesion(args, kwargs, func)

      
        if usuario.is_superuser:
            return func(*args, **kwargs)

        codigo = codigo_fijo or _codigo_deducido(func)
        if codigo is None:
          
            raise GraphQLError(
                f"'{func.__name__}' tiene @requiere_permiso pero su clase no "
                f"tiene @auto_permisos, así que no se sabe qué permiso pedir. "
                f'Coloque @auto_permisos(recurso="...") en la clase, o pásele el '
                f'código: @requiere_permiso("mi_codigo").'
            )

        _exigir_codigo(usuario, codigo)
        return func(*args, **kwargs)

    
    guard._codigo_permiso = codigo_fijo
    guard._requiere_permiso = True
    return guard


def _codigo_deducido(func) -> str | None:
    """Es EL MISMO cálculo que hace el generador, así que no se pueden
    desincronizar: los dos salen de la clase donde el método está DEFINIDO.

    Esa última parte es el invariante, no un detalle. Si el escáner mirara
    también las clases que solo componen, generaría permisos que acá no se van
    a pedir nunca. Ver `scanner._declara_permisos`."""
    propia = getattr(func, METADATA, None)
    if propia is not None:
        return codename_de(propia["recurso"], propia["operacion"])

    clase = _clase_de(func)
    marca = getattr(clase, "_auto_permiso_clase", None) if clase else None
    if marca is None:
        return None

    return codename_de(marca["recurso"], func.__name__)


def _clase_de(funcion):
    """Se resuelve al LLAMAR y no al decorar: cuando el decorador corre, la
    clase todavía no existe."""
    import sys

    partes = getattr(funcion, "__qualname__", "").split(".")
    if len(partes) < 2:
        return None

    modulo = sys.modules.get(funcion.__module__)
    return getattr(modulo, partes[-2], None) if modulo else None


def solo_proveedor(func):
    """La cuenta no tiene que pertenecer a ningún cliente.

    Va sobre las mutations del catálogo del sistema —monedas, países,
    idiomas—: un permiso suelto no alcanza porque se le puede dar a un
    cliente por error, y ninguno debería crear monedas para los demás.

    Pregunta por `matriz` y no por `is_staff`: aquel significa "entra al
    /admin/ de Django", que no es lo mismo — hay gente del proveedor que
    no lo necesita."""

    @functools.wraps(func)
    def guard(*args, **kwargs):
        usuario = _exigir_sesion(args, kwargs, func)

        if getattr(usuario, "matriz_id", None) is not None:
            
            raise GraphQLError(SIN_PERMISO, extensions={"code": CODIGO_SIN_PERMISO})

        return func(*args, **kwargs)

    guard._solo_proveedor = True
    return guard


__all__ = [
    "usuario_de_la_sesion",
    "usuario_de_request",
    "exigir_permiso",
    "requiere_autenticacion",
    "requiere_permiso",
    "solo_proveedor",
    "SIN_PERMISO",
    "SIN_SESION",
    "CODIGO_SIN_PERMISO",
    "CODIGO_SIN_SESION",
]
