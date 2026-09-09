from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias.constantes import AGRUPADOR
from dominios.entidades.models import Entidad
from dominios.entidades.repository import entidad as repo
from dominios.entidades.services import _comun


def _normalizar_documento(documento: str | None) -> str:
    """
    Sin espacios alrededor, y `None` es lo mismo que vacío.

    No es cosmético: `" 1234567 "` y `"1234567"` son documentos distintos
    para la constraint, así que sin esto el duplicado entra igual.
    """
    return (documento or "").strip()


def _validar_documento(documento: str, excluir_id: int | None = None) -> None:
    if repo.existe_documento(documento, excluir_id):
        raise ValidationError(
            f"Ya hay una entidad con el documento '{documento}' en esta empresa."
        )


@transaction.atomic
def crear(
    *,
    tipo_entidad_id: int,
    nombre: str,
    tipo_documento_id: int,
    estado_id: int,
    pri_apellido: str = "",
    seg_apellido: str = "",
    documento: str = "",
    regimen_tributario_id: int | None = None,
) -> Entidad:
    """No recibe `empresa_id` y nunca lo va a recibir: sale del contexto."""
    _comun.validar_tipo(tipo_entidad_id, AGRUPADOR.TIPO_ENTIDAD)
    _comun.validar_tipo(tipo_documento_id, AGRUPADOR.TIPO_DOCUMENTO)
    _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)
    if regimen_tributario_id is not None:
        _comun.validar_tipo(regimen_tributario_id, AGRUPADOR.REGIMEN_TRIBUTARIO)

    documento = _normalizar_documento(documento)
    _validar_documento(documento)

    return repo.crear(
        tipo_entidad_id=tipo_entidad_id,
        nombre=nombre,
        pri_apellido=pri_apellido,
        seg_apellido=seg_apellido,
        tipo_documento_id=tipo_documento_id,
        documento=documento,
        regimen_tributario_id=regimen_tributario_id,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    entidad_id: int,
    *,
    tipo_entidad_id: int | None = None,
    nombre: str | None = None,
    pri_apellido: str | None = None,
    seg_apellido: str | None = None,
    tipo_documento_id: int | None = None,
    documento: str | None = None,
    regimen_tributario_id: int | None = None,
    estado_id: int | None = None,
) -> Entidad:
    fila = _comun.entidad(entidad_id)

    if tipo_entidad_id is not None:
        _comun.validar_tipo(tipo_entidad_id, AGRUPADOR.TIPO_ENTIDAD)
    if tipo_documento_id is not None:
        _comun.validar_tipo(tipo_documento_id, AGRUPADOR.TIPO_DOCUMENTO)
    if regimen_tributario_id is not None:
        _comun.validar_tipo(regimen_tributario_id, AGRUPADOR.REGIMEN_TRIBUTARIO)
    if estado_id is not None:
        _comun.validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO)

    if documento is not None:
        documento = _normalizar_documento(documento)
        _validar_documento(documento, excluir_id=entidad_id)

    campos = _comun.solo_los_dados(
        tipo_entidad_id=tipo_entidad_id,
        nombre=nombre,
        pri_apellido=pri_apellido,
        seg_apellido=seg_apellido,
        tipo_documento_id=tipo_documento_id,
        documento=documento,
        regimen_tributario_id=regimen_tributario_id,
        estado_id=estado_id,
    )
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(entidad_id: int) -> Entidad:
    """
    Soft delete. Nada se borra físicamente en este ERP.

     NO cascadea a los roles ni a las direcciones, a propósito: una
    entidad de baja con sus roles intactos se puede reactivar y queda
    como estaba. Si algún día hay que bajarlos también, es una decisión
    del negocio y va escrita acá, no implícita.
    """
    fila = _comun.entidad(entidad_id)
    return repo.actualizar(fila, estado_id=_comun.estado_de_baja().pk)
