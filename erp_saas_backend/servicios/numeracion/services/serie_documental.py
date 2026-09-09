from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from servicios.numeracion.models import SerieDocumental
from servicios.numeracion.repository import correlativo as repo_correlativo
from servicios.numeracion.repository import serie_documental as repo


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )


def _validar_tipo_documento(tipo_documento_id: int):
    """
    Aislamiento: se resuelve contra el queryset ya filtrado, no por id crudo.
    `TipoDocumentoComercial` es tenant, así que uno de otra empresa no
    aparece — y el mensaje dice "no existe", no "no es tuyo".
    """
    from comun.tipos_documento import api as tipos_documento

    fila = tipos_documento.obtener(tipo_documento_id)
    if fila is None:
        raise ValidationError(
            f"No existe el tipo de documento {tipo_documento_id}."
        )
    return fila


@transaction.atomic
def crear(*, tipo_documento_id: int, estado_id: int, prefijo: str = "") -> SerieDocumental:
    _validar_tipo_documento(tipo_documento_id)
    _validar_estado(estado_id)

    prefijo = (prefijo or "").strip()

    if repo.existe(tipo_documento_id, prefijo):
        raise ValidationError(
            f"Ya hay una serie de ese tipo de documento con el prefijo "
            f"'{prefijo}' en esta empresa."
        )

    return repo.crear(
        tipo_documento_id=tipo_documento_id,
        prefijo=prefijo,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    serie_id: int, *, prefijo: str | None = None, estado_id: int | None = None
) -> SerieDocumental:
    """
    `tipo_documento` no se cambia: sería otra serie. El prefijo tampoco,
    si la serie ya numeró algo.
    """
    serie = repo.obtener(serie_id)
    if serie is None:
        raise ValidationError(f"No existe la serie documental {serie_id}.")

    if estado_id is not None:
        _validar_estado(estado_id)

    campos = {}

    if prefijo is not None:
        prefijo = prefijo.strip()
        if prefijo != serie.prefijo:
            if repo_correlativo.listar_de_serie(serie_id):
                raise ValidationError(
                    "Esta serie ya emitió documentos: cambiarle el prefijo "
                    "haría que lo impreso no coincida con lo que el sistema "
                    "calcula. Creá una serie nueva."
                )
            if repo.existe(serie.tipo_documento_id, prefijo, excluir_id=serie_id):
                raise ValidationError(
                    f"Ya hay una serie de ese tipo con el prefijo '{prefijo}'."
                )
            campos["prefijo"] = prefijo

    if estado_id is not None:
        campos["estado_id"] = estado_id

    if not campos:
        return serie

    return repo.actualizar(serie, **campos)


@transaction.atomic
def desactivar(serie_id: int) -> SerieDocumental:
    """
    Soft delete. Los correlativos NO se borran: son el registro de qué
    números se emitieron, y eso no se puede perder.
    """
    serie = repo.obtener(serie_id)
    if serie is None:
        raise ValidationError(f"No existe la serie documental {serie_id}.")

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Corré: python manage.py cargar_semillas"
        )

    return repo.actualizar(serie, estado_id=baja.pk)
