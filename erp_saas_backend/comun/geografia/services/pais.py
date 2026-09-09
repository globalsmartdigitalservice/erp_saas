from django.core.exceptions import ValidationError
from django.db import transaction

from comun.geografia.models import Pais
from comun.geografia.repository import pais as repo
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado de país"
    )


def _validar_codigos(codigo_iso: str, cod_pais: str, excluir_id: int | None = None) -> None:
    if repo.existe_codigo_iso(codigo_iso, excluir_id):
        raise ValidationError(f"Ya existe un país con el código ISO '{codigo_iso}'.")
    if repo.existe_cod_pais(cod_pais, excluir_id):
        raise ValidationError(f"Ya existe un país con el código '{cod_pais}'.")


@transaction.atomic
def crear(*, cod_pais: str, nombre: str, codigo_iso: str, estado_id: int) -> Pais:
    _validar_estado(estado_id)
    _validar_codigos(codigo_iso, cod_pais)

    return repo.crear(
        cod_pais=cod_pais,
        nombre=nombre,
        codigo_iso=codigo_iso,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    pais_id: int,
    *,
    cod_pais: str | None = None,
    nombre: str | None = None,
    codigo_iso: str | None = None,
    estado_id: int | None = None,
) -> Pais:
    pais = repo.obtener(pais_id)
    if pais is None:
        raise ValidationError(f"No existe el país {pais_id}.")

    if estado_id is not None:
        _validar_estado(estado_id)

    _validar_codigos(
        codigo_iso if codigo_iso is not None else pais.codigo_iso,
        cod_pais if cod_pais is not None else pais.cod_pais,
        excluir_id=pais_id,
    )

    campos = {
        campo: valor
        for campo, valor in (
            ("cod_pais", cod_pais),
            ("nombre", nombre),
            ("codigo_iso", codigo_iso),
            ("estado_id", estado_id),
        )
        if valor is not None
    }
    if not campos:
        return pais

    return repo.actualizar(pais, **campos)


@transaction.atomic
def desactivar(pais_id: int) -> Pais:
    """
    Soft delete. En este ERP nada se borra físicamente: se desactiva
    (repetido en cada entidad).
    """
    pais = repo.obtener(pais_id)
    if pais is None:
        raise ValidationError(f"No existe el país {pais_id}.")

    inactivo = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if inactivo is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Corré: python manage.py cargar_semillas"
        )

    return repo.actualizar(pais, estado_id=inactivo.pk)
