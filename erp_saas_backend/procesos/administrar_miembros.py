"""Dar de baja y desactivar sin dejar una empresa sin quien la administre."""

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
from comun.usuarios import api as usuarios
from core.tenancy import empresa as contexto_empresa
from dominios.seguridad import api as seguridad


def membresias_vigentes_de(usuario_id: int):
    """Las membresías activas de la persona, en todas las empresas del cliente."""
    activo = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
    )
    if activo is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_ACTIVO}'. "
            f"Ejecute: python manage.py cargar_semillas"
        )
    return membresias.membresias_de_usuario(usuario_id, activo.pk)


@transaction.atomic
def desafiliar(*, membresia_id: int, estado_baja_id: int, fecha_finalizacion=None):
    seguridad.exigir_que_quede_quien_administre(excluir_membresia_id=membresia_id)
    return membresias.desafiliar(
        membresia_id=membresia_id,
        estado_baja_id=estado_baja_id,
        fecha_finalizacion=fecha_finalizacion,
    )


@transaction.atomic
def desactivar_cuenta(usuario_id: int):
    """Revisa cada empresa de la persona antes de apagarle la cuenta."""
    for membresia in membresias_vigentes_de(usuario_id):
        with contexto_empresa(membresia.empresa_id):
            seguridad.exigir_que_quede_quien_administre(
                excluir_membresia_id=membresia.pk
            )
    return usuarios.desactivar_usuario(usuario_id)


__all__ = ["membresias_vigentes_de", "desafiliar", "desactivar_cuenta"]
