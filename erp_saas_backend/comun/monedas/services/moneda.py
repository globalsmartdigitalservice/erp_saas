from django.core.exceptions import ValidationError
from django.db import transaction

from comun.monedas.models import Moneda
from comun.monedas.repository import moneda as repo
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA


LARGO_CODIGO = 3


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado de moneda"
    )


def _normalizar_codigo(codigo: str) -> str:
    """`usd` y ` USD ` son la misma moneda. Se guarda una sola forma."""
    return (codigo or "").strip().upper()


def _validar_codigo(codigo: str, excluir_id: int | None = None) -> None:
    if len(codigo) != LARGO_CODIGO or not (codigo.isascii() and codigo.isalpha()):
        raise ValidationError(
            f"El código de moneda son {LARGO_CODIGO} letras, como en ISO 4217"
            f" ('BOB', 'USD'). Recibido: '{codigo}'."
        )
    if repo.existe_codigo(codigo, excluir_id):
        raise ValidationError(f"Ya existe una moneda con el código '{codigo}'.")


def _obtener_o_fallar(moneda_id: int) -> Moneda:
    moneda = repo.obtener(moneda_id)
    if moneda is None:
        raise ValidationError(f"No existe la moneda {moneda_id}.")
    return moneda


@transaction.atomic
def crear(
    *,
    descripcion: str,
    codigo: str,
    simbolo: str = "",
    estado_id: int,
) -> Moneda:
    """
    Alta de una moneda en el catálogo. No dice nada de quién la usa:
    eso es `empresas.agregar_moneda()`.
    """
    _validar_estado(estado_id)
    codigo = _normalizar_codigo(codigo)
    _validar_codigo(codigo)

    return repo.crear(
        descripcion=descripcion,
        codigo=codigo,
        simbolo=simbolo,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    moneda_id: int,
    *,
    descripcion: str | None = None,
    codigo: str | None = None,
    simbolo: str | None = None,
    estado_id: int | None = None,
) -> Moneda:
    moneda = _obtener_o_fallar(moneda_id)

    if estado_id is not None:
        _validar_estado(estado_id)

    if codigo is not None:
        codigo = _normalizar_codigo(codigo)
        _validar_codigo(codigo, excluir_id=moneda_id)

    campos = {}
    for campo, valor in (
        ("descripcion", descripcion),
        ("codigo", codigo),
        ("simbolo", simbolo),
        ("estado_id", estado_id),
    ):
        if valor is not None:
            campos[campo] = valor

    if not campos:
        return moneda

    return repo.actualizar(moneda, **campos)


@transaction.atomic
def desactivar(moneda_id: int) -> Moneda:
    """
    Soft delete. En este ERP nada se borra físicamente: se desactiva
    (repetido en cada entidad).

     Acá ya NO se pregunta si es "la oficial": en el modelo de datos eso es por
    empresa y vive en `empresa_moneda`. Lo que sí se pregunta es si
    ALGUNA empresa la está usando — es el heredero del invariante viejo,
    y el mismo trato que recibe el idioma por defecto.

    El import va adentro de la función a propósito: `empresas` importa
    de vuelta a `monedas` (su `empresa_moneda` necesita el catálogo),
    así que al tope se haría circular.
    """
    from comun.empresas import api as empresas

    moneda = _obtener_o_fallar(moneda_id)

    if empresas.hay_empresas_con_moneda(moneda_id):
        raise ValidationError(
            f"'{moneda.codigo}' la está usando alguna empresa: no se puede "
            f"sacar del catálogo. Quítesela a esas empresas primero."
        )

    inactivo = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if inactivo is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Ejecute: python manage.py cargar_semillas"
        )

    return repo.actualizar(moneda, estado_id=inactivo.pk)
