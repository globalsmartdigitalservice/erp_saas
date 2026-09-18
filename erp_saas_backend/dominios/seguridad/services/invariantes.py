"""La empresa nunca queda sin quien pueda asignar roles."""

import functools

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas import api as empresas
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
from core.tenancy import empresa_actual
from dominios.seguridad.permisos import codename_de
from dominios.seguridad.repository import grupo_usuario as repo


LLAVE_DE_ADMINISTRACION = codename_de("SEGU_ROLES", "asignar_rol")

ULTIMA_PERSONA = (
    "Es la última persona que puede administrar {empresa}. Asigne a otra "
    "persona un rol que lo permita antes de continuar."
)


def hay_quien_administre() -> bool:
    """Quien administra sin fecha de fin: el que vence no cuenta."""
    activo = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
    )
    if activo is None:
        return False
    return repo.hay_permanente_con_permiso(LLAVE_DE_ADMINISTRACION, activo.pk)


def preserva_quien_administra(func):
    """Revierte la operación si la empresa se quedó sin quien administre."""

    @functools.wraps(func)
    @transaction.atomic
    def _con_compuerta(*args, **kwargs):
        habia = hay_quien_administre()
        resultado = func(*args, **kwargs)
        if habia and not hay_quien_administre():
            empresa = empresas.obtener_empresa(empresa_actual())
            raise ValidationError(ULTIMA_PERSONA.format(empresa=empresa.razon_social))
        return resultado

    return _con_compuerta
