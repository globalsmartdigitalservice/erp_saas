"""Da de alta a una persona en la empresa de la sesión: su cuenta, su membresía y sus roles."""

import dataclasses

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
from comun.usuarios import api as usuarios
from dominios.seguridad import api as seguridad


@dataclasses.dataclass(frozen=True)
class PersonaNueva:
    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    seg_apellido: str = ""
    password: str | None = None


class MiembroNuevo:
    """`password_temporal` solo viene si la generó el sistema, y se muestra una vez."""

    def __init__(self, *, membresia, usuario, password_temporal):
        self.membresia = membresia
        self.usuario = usuario
        self.password_temporal = password_temporal


def _estado_activo() -> int:
    activo = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
    )
    if activo is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_ACTIVO}'. "
            f"Ejecute: python manage.py cargar_semillas"
        )
    return activo.pk


@transaction.atomic
def dar_de_alta(
    *,
    usuario_id: int | None = None,
    persona: PersonaNueva | None = None,
    rol_ids=(),
    asignado_por_id: int | None = None,
) -> MiembroNuevo:
    """Todo o nada: si falla un paso, no quedan ni la cuenta ni la membresía."""
    if (usuario_id is None) == (persona is None):
        raise ValidationError(
            "Indique una persona que ya existe o los datos de una nueva: una de las dos."
        )

    estado_id = _estado_activo()
    password_temporal = None

    if persona is not None:
        if not persona.password:
            password_temporal = usuarios.generar_password_temporal()
        cuenta = usuarios.crear_usuario(
            username=persona.username,
            email=persona.email,
            password=persona.password or password_temporal,
            first_name=persona.first_name,
            last_name=persona.last_name,
            seg_apellido=persona.seg_apellido,
        )
        usuario_id = cuenta.pk

    membresia = membresias.afiliar(usuario_id=usuario_id, estado_id=estado_id)

    for rol_id in dict.fromkeys(rol_ids):
        seguridad.asignar_rol(
            membresia_id=membresia.pk,
            grupo_id=rol_id,
            estado_id=estado_id,
            asignado_por_id=asignado_por_id,
        )

    return MiembroNuevo(
        membresia=membresia,
        usuario=usuarios.obtener_usuario(usuario_id),
        password_temporal=password_temporal,
    )


__all__ = ["dar_de_alta", "PersonaNueva", "MiembroNuevo"]
