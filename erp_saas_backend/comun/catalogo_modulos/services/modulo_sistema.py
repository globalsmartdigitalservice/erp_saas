from django.core.exceptions import ValidationError
from django.db import transaction

from comun.catalogo_modulos.models import ModuloSistema
from comun.catalogo_modulos.repository import modulo_dependencia as repo_dep
from comun.catalogo_modulos.repository import modulo_sistema as repo
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )


def _normalizar(codigo: str) -> str:
    return (codigo or "").strip().upper()


@transaction.atomic
def crear(
    *,
    codigo: str,
    nombre: str,
    estado_id: int,
    version: str = "",
    es_vendible: bool = False,
) -> ModuloSistema:
    _validar_estado(estado_id)

    codigo = _normalizar(codigo)
    if not codigo:
        raise ValidationError("El código del módulo no puede ir vacío.")
    if repo.existe_codigo(codigo):
        raise ValidationError(f"Ya existe un módulo con el código '{codigo}'.")

    return repo.crear(
        codigo=codigo,
        nombre=nombre,
        version=version,
        es_vendible=es_vendible,
        estado_id=estado_id,
    )


@transaction.atomic
def actualizar(
    modulo_id: int,
    *,
    codigo: str | None = None,
    nombre: str | None = None,
    version: str | None = None,
    es_vendible: bool | None = None,
    estado_id: int | None = None,
) -> ModuloSistema:
    fila = repo.obtener(modulo_id)
    if fila is None:
        raise ValidationError(f"No existe el módulo {modulo_id}.")

    if estado_id is not None:
        _validar_estado(estado_id)

    if codigo is not None:
        codigo = _normalizar(codigo)
        if repo.existe_codigo(codigo, excluir_id=modulo_id):
            raise ValidationError(f"Ya existe un módulo con el código '{codigo}'.")

    campos = {
        campo: valor
        for campo, valor in (
            ("codigo", codigo),
            ("nombre", nombre),
            ("version", version),
            ("es_vendible", es_vendible),
            ("estado_id", estado_id),
        )
        if valor is not None
    }
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)


@transaction.atomic
def desactivar(modulo_id: int) -> ModuloSistema:
    fila = repo.obtener(modulo_id)
    if fila is None:
        raise ValidationError(f"No existe el módulo {modulo_id}.")

    dependientes = repo_dep.listar_que_dependen_de(modulo_id)
    if dependientes:
        codigos = sorted(d.modulo.codigo for d in dependientes)
        raise ValidationError(
            f"No se puede dar de baja '{fila.codigo}': lo necesitan "
            f"{', '.join(codigos)}. Quitá primero esas dependencias."
        )

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Corré: python manage.py cargar_semillas"
        )

    return repo.actualizar(fila, estado_id=baja.pk)
