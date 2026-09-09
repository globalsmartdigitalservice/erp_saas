from django.core.exceptions import ValidationError
from django.db import transaction

from comun.catalogo_modulos import api as modulos
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from servicios.integraciones.models import ReferenciaCruzada
from servicios.integraciones.repository import referencia_cruzada as repo


def _validar_tipo(tipologia_id: int, agrupador: int, que_es: str) -> None:
    """`que_es` va SIN artículo: lo pone `exigir_del_agrupador`."""
    tipologias.exigir_del_agrupador(tipologia_id, agrupador, que_es)


def _validar_modulo(codigo: str, cual: str) -> str:
    codigo = (codigo or "").strip().upper()
    if not codigo:
        raise ValidationError(f"Falta el código del módulo de {cual}.")

    if modulos.obtener_por_codigo(codigo) is None:
        raise ValidationError(
            f"No existe el módulo '{codigo}'. El código de {cual} tiene que ser "
            f"uno de los declarados en el catálogo de módulos."
        )
    return codigo


@transaction.atomic
def vincular(
    *,
    modulo_origen: str,
    tabla_origen: str,
    registro_origen_id: int,
    modulo_destino: str,
    tabla_destino: str,
    registro_destino_id: int,
    tipo_vinculo_id: int,
    estado_id: int,
) -> ReferenciaCruzada:
    modulo_origen = _validar_modulo(modulo_origen, "origen")
    modulo_destino = _validar_modulo(modulo_destino, "destino")

    _validar_tipo(tipo_vinculo_id, AGRUPADOR.TIPO_VINCULO, "tipo de vínculo")
    _validar_tipo(estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro")

    if (tabla_origen, registro_origen_id) == (tabla_destino, registro_destino_id):
        raise ValidationError(
            "Un registro no se vincula consigo mismo: el vínculo no diría nada."
        )

    if repo.existe(
        tabla_origen=tabla_origen,
        registro_origen_id=registro_origen_id,
        tabla_destino=tabla_destino,
        registro_destino_id=registro_destino_id,
        tipo_vinculo_id=tipo_vinculo_id,
    ):
        raise ValidationError("Ese vínculo ya está registrado.")

    return repo.crear(
        modulo_origen=modulo_origen,
        tabla_origen=tabla_origen,
        registro_origen_id=registro_origen_id,
        modulo_destino=modulo_destino,
        tabla_destino=tabla_destino,
        registro_destino_id=registro_destino_id,
        tipo_vinculo_id=tipo_vinculo_id,
        estado_id=estado_id,
    )


@transaction.atomic
def anular(vinculo_id: int) -> ReferenciaCruzada:
    """
    Soft delete. **Un vínculo anulado sigue siendo historia**: dice que
    alguna vez esos dos registros estuvieron relacionados, y eso importa
    cuando hay que reconstruir qué pasó.
    """
    fila = repo.obtener(vinculo_id)
    if fila is None:
        raise ValidationError(f"No existe el vínculo {vinculo_id}.")

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Ejecute: python manage.py cargar_semillas"
        )

    return repo.actualizar(fila, estado_id=baja.pk)
