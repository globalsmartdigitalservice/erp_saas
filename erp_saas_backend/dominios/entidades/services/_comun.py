from django.core.exceptions import ValidationError

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from dominios.entidades.repository import entidad as _repo_entidad

# Para los mensajes: cómo se llama el campo que se esperaba.
#
# SIN el artículo: lo pone `exigir_del_agrupador`, que arma la frase
# "Se esperaba un {esto}". Con el artículo acá quedaba "un un tipo de rol".
_LISTAS = {
    AGRUPADOR.TIPO_ENTIDAD: "tipo de entidad",
    AGRUPADOR.TIPO_DOCUMENTO: "tipo de documento",
    AGRUPADOR.TIPO_ROL: "tipo de rol",
    AGRUPADOR.TIPO_DIRECCION: "tipo de dirección",
    AGRUPADOR.REGIMEN_TRIBUTARIO: "régimen tributario",
    AGRUPADOR.ESTADO_REGISTRO: "estado del registro",
}


def validar_tipo(tipologia_id: int, agrupador: int) -> None:
    """
     `es_del_agrupador` consulta por el manager de `Tipologia`, que ya
    es multiempresa: ve las de fábrica, las propias y las heredadas de la
    matriz, y descuenta las ocultas. O sea que esta función cierra los
    DOS agujeros a la vez — el de la lista equivocada y el de la tipología
    de otra empresa.
    """
    tipologias.exigir_del_agrupador(
        tipologia_id, agrupador, _LISTAS.get(agrupador, "valor de esa lista")
    )


def entidad(entidad_id: int):
    """La entidad de la empresa activa, o un error. Nunca la de otra."""
    fila = _repo_entidad.obtener(entidad_id)
    if fila is None:
        raise ValidationError(f"No existe la entidad {entidad_id}.")
    return fila


def estado_de_baja():
    """La fila compartida del soft delete."""
    fila = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if fila is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Corré: python manage.py cargar_semillas"
        )
    return fila


def solo_los_dados(**campos) -> dict:
    """Los campos que llegaron con valor. `None` = "no lo toques"."""
    return {campo: valor for campo, valor in campos.items() if valor is not None}
