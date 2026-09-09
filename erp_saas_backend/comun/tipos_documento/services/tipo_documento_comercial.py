from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from comun.tipos_documento.models import TipoDocumentoComercial
from comun.tipos_documento.repository import tipo_documento_comercial as repo


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )


def _normalizar(codigo: str) -> str:
    """Sin espacios y en mayúsculas: es un código, no un texto."""
    return (codigo or "").strip().upper()


@transaction.atomic
def crear(
    *,
    codigo: str,
    nombre: str,
    estado_id: int,
    afecta_stock: bool = False,
    genera_ingreso: bool = False,
    es_venta: bool = False,
) -> TipoDocumentoComercial:
    _validar_estado(estado_id)

    codigo = _normalizar(codigo)
    if not codigo:
        raise ValidationError("El código del tipo de documento no puede ir vacío.")
    if repo.existe_codigo(codigo):
        raise ValidationError(
            f"Ya hay un tipo de documento con el código '{codigo}' en esta empresa."
        )

    return repo.crear(
        codigo=codigo,
        nombre=nombre,
        afecta_stock=afecta_stock,
        genera_ingreso=genera_ingreso,
        es_venta=es_venta,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    tipo_id: int,
    *,
    codigo: str | None = None,
    nombre: str | None = None,
    afecta_stock: bool | None = None,
    genera_ingreso: bool | None = None,
    es_venta: bool | None = None,
    estado_id: int | None = None,
) -> TipoDocumentoComercial:
    fila = repo.obtener(tipo_id)
    if fila is None:
        raise ValidationError(f"No existe el tipo de documento {tipo_id}.")

    if estado_id is not None:
        _validar_estado(estado_id)

    if codigo is not None:
        codigo = _normalizar(codigo)
        if repo.existe_codigo(codigo, excluir_id=tipo_id):
            raise ValidationError(
                f"Ya hay un tipo de documento con el código '{codigo}'."
            )

    campos = {
        campo: valor
        for campo, valor in (
            ("codigo", codigo),
            ("nombre", nombre),
            ("afecta_stock", afecta_stock),
            ("genera_ingreso", genera_ingreso),
            ("es_venta", es_venta),
            ("estado_id", estado_id),
        )
        if valor is not None
    }
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(tipo_id: int) -> TipoDocumentoComercial:
    fila = repo.obtener(tipo_id)
    if fila is None:
        raise ValidationError(f"No existe el tipo de documento {tipo_id}.")

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Corré: python manage.py cargar_semillas"
        )

    return repo.actualizar(fila, estado_id=baja.pk)
