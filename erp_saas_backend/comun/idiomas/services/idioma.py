import re

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas import api as empresas
from comun.idiomas.models import Idioma
from comun.idiomas.repository import idioma as repo

# dos o tres letras, y opcionalmente una región de dos: es · qu · es-bo
FORMA_CODIGO = re.compile(r"^[a-z]{2,3}(-[a-z]{2})?$")


def _normalizar_codigo(codigo: str) -> str:
    """`ES` y `es` son el mismo idioma. Se guarda una sola forma."""
    return (codigo or "").strip().lower()


def _validar_codigo(codigo: str, excluir_id: int | None = None) -> None:
    if not FORMA_CODIGO.match(codigo):
        raise ValidationError(
            f"El código de idioma es una etiqueta como 'es', 'en' o 'es-bo' "
            f"(ISO 639-1, con región opcional). Recibido: '{codigo}'."
        )
    if repo.existe_codigo(codigo, excluir_id):
        raise ValidationError(f"Ya existe un idioma con el código '{codigo}'.")


def _obtener_o_fallar(idioma_id: int) -> Idioma:
    idioma = repo.obtener(idioma_id)
    if idioma is None:
        raise ValidationError(f"No existe el idioma {idioma_id}.")
    return idioma


@transaction.atomic
def crear(*, codigo: str, nombre: str, activo: bool = True) -> Idioma:
    codigo = _normalizar_codigo(codigo)
    _validar_codigo(codigo)

    return repo.crear(codigo=codigo, nombre=nombre, activo=activo)


@transaction.atomic
def actualizar(
    idioma_id: int, *, codigo: str | None = None, nombre: str | None = None
) -> Idioma:
    """
    Cambia los datos de un idioma.

    `activo` NO es parámetro y no lo va a ser: prender y apagar tiene
    sus propias funciones, para que la intención quede escrita en el
    nombre de lo que se llama y no escondida en un campo más del input.
    """
    idioma = _obtener_o_fallar(idioma_id)

    if codigo is not None:
        codigo = _normalizar_codigo(codigo)
        _validar_codigo(codigo, excluir_id=idioma_id)

    campos = {
        campo: valor
        for campo, valor in (("codigo", codigo), ("nombre", nombre))
        if valor is not None
    }
    if not campos:
        return idioma

    return repo.actualizar(idioma, **campos)


@transaction.atomic
def desactivar(idioma_id: int) -> Idioma:
    """
    Soft delete. En este ERP nada se borra físicamente: se desactiva
    (repetido en cada entidad).

    INVARIANTE: no se puede apagar un idioma que alguna empresa esté
    usando como `idioma_default`. La FK es PROTECT, así que un DELETE ya
    revienta — pero desactivarlo NO, y dejaría empresas apuntando a un
    idioma apagado sin ningún aviso.

    La pregunta "¿hay empresas con este idioma?" la contesta
    `comun/empresas` por su `api.py`: acá no se importa ningún modelo
    ajeno, solo se cruza la frontera de módulo.
    """
    idioma = _obtener_o_fallar(idioma_id)

    if not idioma.activo:
        return idioma

    if empresas.hay_empresas_con_idioma(idioma_id):
        raise ValidationError(
            f"'{idioma.nombre}' es el idioma por defecto de al menos una "
            f"empresa: no se puede desactivar. Cámbieles el idioma primero."
        )

    return repo.actualizar(idioma, activo=False)


@transaction.atomic
def activar(idioma_id: int) -> Idioma:
    """
    La vuelta atrás de `desactivar()`.

    Existe porque el borrado lógico de esta tabla es un booleano: no hay
    una tipología "Activo" a la que volver, como en las demás apps.
    """
    idioma = _obtener_o_fallar(idioma_id)

    if idioma.activo:
        return idioma

    return repo.actualizar(idioma, activo=True)
