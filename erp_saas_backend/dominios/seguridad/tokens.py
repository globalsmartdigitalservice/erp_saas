"""Los tokens del login: uno corto para trabajar y uno largo para renovar.

    ACCESO    15 minutos   viaja en cada petición
    REFRESH    7 días      solo se usa para pedir uno nuevo

 LO QUE HACE QUE ESTO NO SEA DECORATIVO: EL LOGOUT. Un JWT vale hasta que
vence y el servidor no lo puede retirar, así que el refresh lleva adentro
el id de una fila de `Sesion_Acceso` y salir le llena el `fin`.

El de acceso NO se comprueba contra la base —sería una consulta por
petición— y por eso dura poco: entre el logout y su vencimiento hay una
ventana de 15 minutos.

ROTACIÓN: cada uso del refresh emite uno nuevo con otro `jti`, así que un
refresh robado sirve una sola vez."""

import datetime
import uuid

import jwt
from django.conf import settings

# `typ` adentro del token. Sin esto, un token de acceso serviría para
# renovar y uno de refresh para trabajar: son el mismo formato firmado
# con la misma clave, así que la única diferencia es lo que dice adentro.
TIPO_ACCESO = "acceso"
TIPO_REFRESH = "refresh"

ALGORITMO = "HS256"


class InvalidTokenError(Exception):
    """Firma que no cierra, vencido, del tipo equivocado o mal formado.

     UNA SOLA excepción para todos los casos: distinguir "vencido" de "firma
    inválida" le diría al cliente si su token fue alguna vez válido."""


def _clave() -> str:
    return settings.SECRET_KEY


def _ahora() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def emitir_acceso(*, usuario_id: int, empresa_id: int, sesion_id: int) -> str:
    """El token de trabajo. Lleva la EMPRESA adentro, y eso es lo que hace
    que el aislamiento funcione sin preguntar en cada petición. Por eso
    cambiar de empresa exige un token nuevo, no un parámetro."""
    ahora = _ahora()
    return jwt.encode(
        {
            "typ": TIPO_ACCESO,
            "sub": str(usuario_id),
            "emp": empresa_id,
            "ses": sesion_id,
            "iat": ahora,
            "exp": ahora + settings.JWT_VIDA_ACCESO,
        },
        _clave(),
        algorithm=ALGORITMO,
    )


def emitir_refresh(*, usuario_id: int, empresa_id: int, sesion_id: int) -> tuple[str, str]:
    """El token de renovación. Devuelve `(token, jti)`: el `jti` se guarda en
    la sesión y es lo que permite la rotación."""
    ahora = _ahora()
    jti = uuid.uuid4().hex
    token = jwt.encode(
        {
            "typ": TIPO_REFRESH,
            "sub": str(usuario_id),
            "emp": empresa_id,
            "ses": sesion_id,
            "jti": jti,
            "iat": ahora,
            "exp": ahora + settings.JWT_VIDA_REFRESH,
        },
        _clave(),
        algorithm=ALGORITMO,
    )
    return token, jti


def leer(token: str, *, tipo: str) -> dict:
    """Verifica la firma, el vencimiento y el tipo.

     `tipo` no es opcional: sin comprobarlo, un token de acceso —mucho más
    fácil de conseguir— serviría para renovar la sesión indefinidamente."""
    try:
        datos = jwt.decode(token, _clave(), algorithms=[ALGORITMO])
    except jwt.PyJWTError as error:
        raise InvalidTokenError(str(error)) from error

    if datos.get("typ") != tipo:
        raise InvalidTokenError(f"Se esperaba un token de {tipo}.")

    return datos


__all__ = [
    "emitir_acceso",
    "emitir_refresh",
    "leer",
    "InvalidTokenError",
    "TIPO_ACCESO",
    "TIPO_REFRESH",
]
