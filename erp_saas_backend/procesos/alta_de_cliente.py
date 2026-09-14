"""El alta de un cliente: la empresa y su primer administrador, juntos.

Lo corre el proveedor, que no tiene sesión ni empresa, y `crear_usuario()` saca
el cliente del contexto: por eso se crea la empresa primero y el proceso se para
adentro de ella. Todo en una transacción, porque una empresa sin administrador
es el agujero que este proceso cierra.
"""

import dataclasses

from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas import api as empresas
from comun.empresas.services.empresa import (
    NOMBRE_ESTADO_ACTIVA,
    NOMBRE_TIPO_MATRIZ,
)
from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
from comun.usuarios import api as usuarios
from core.tenancy import empresa as contexto_empresa
from dominios.seguridad import api as seguridad
from dominios.seguridad.permisos import content_type_del_ancla

NOMBRE_DEL_ROL_INICIAL = "Administrador"


@dataclasses.dataclass(frozen=True)
class DatosDelCliente:
    """Lo que cambia de un cliente a otro. El tipo y el estado NO están acá:
    todo cliente nace como casa matriz y activa, y eso lo decide el proceso."""

    ident_tributaria: str
    razon_social: str
    rubro_id: int
    pais_id: int
    moneda_oficial_id: int
    idioma_default_id: int
    nombre_comercial: str = ""


@dataclasses.dataclass(frozen=True)
class DatosDelAdministrador:
    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    seg_apellido: str = ""


class ClienteNuevo:
    """Lo que quedó creado. `password_temporal` se muestra UNA vez y no se
    guarda en claro en ningún lado."""

    def __init__(self, *, empresa, administrador, membresia, rol, password_temporal):
        self.empresa = empresa
        self.administrador = administrador
        self.membresia = membresia
        self.rol = rol
        self.password_temporal = password_temporal


def _tipologia(agrupador: int, nombre: str):
    fila = tipologias.obtener_del_sistema(agrupador, nombre)
    if fila is None:
        raise ValidationError(
            f"Falta la tipología '{nombre}'. Ejecute: python manage.py cargar_semillas"
        )
    return fila


def _permisos_del_catalogo() -> list[int]:
    """Los permisos del ERP, que cuelgan todos del mismo ancla.

    Si está vacío se corta: un rol sin permisos deja al administrador del
    cliente entrando a un sistema donde no ve absolutamente nada, y eso se
    descubre tarde y del lado del cliente."""
    ids = list(
        Permission.objects.filter(
            content_type=content_type_del_ancla()
        ).values_list("pk", flat=True)
    )
    if not ids:
        raise ValidationError(
            "El catálogo de permisos está vacío, así que el administrador "
            "entraría sin ver nada. Ejecute: python manage.py generar_permisos"
        )
    return ids


@transaction.atomic
def dar_de_alta(
    *,
    cliente: DatosDelCliente,
    administrador: DatosDelAdministrador,
    password: str | None = None,
) -> ClienteNuevo:
    """Crea la empresa, la cuenta del primer administrador, su membresía y su
    rol con todos los permisos. O entra todo, o no entra nada.

    El proveedor NUNCA queda afiliado: la membresía que se crea es la del
    administrador del cliente. Si después necesita entrar, es por el acceso de
    soporte, que deja rastro."""
    empresa = empresas.crear_empresa(
        ident_tributaria=cliente.ident_tributaria,
        razon_social=cliente.razon_social,
        nombre_comercial=cliente.nombre_comercial,
        tipo_empresa_id=_tipologia(AGRUPADOR.TIPO_EMPRESA, NOMBRE_TIPO_MATRIZ).pk,
        rubro_id=cliente.rubro_id,
        estado_id=_tipologia(AGRUPADOR.ESTADO_EMPRESA, NOMBRE_ESTADO_ACTIVA).pk,
        idioma_default_id=cliente.idioma_default_id,
        moneda_oficial_id=cliente.moneda_oficial_id,
        pais_id=cliente.pais_id,
    )

    activo = _tipologia(AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO)
    temporal = password or usuarios.generar_password_temporal()

    with contexto_empresa(empresa.pk):
        cuenta = usuarios.crear_usuario(
            username=administrador.username,
            email=administrador.email,
            password=temporal,
            first_name=administrador.first_name,
            last_name=administrador.last_name,
            seg_apellido=administrador.seg_apellido,
        )
        membresia = membresias.afiliar(
            usuario_id=cuenta.pk, estado_id=activo.pk
        )
        rol = seguridad.crear_rol(
            nombre=NOMBRE_DEL_ROL_INICIAL, estado_id=activo.pk
        )
        for permiso_id in _permisos_del_catalogo():
            seguridad.agregar_permiso(grupo_id=rol.pk, auth_permission_id=permiso_id)
        seguridad.asignar_rol(
            membresia_id=membresia.pk, grupo_id=rol.pk, estado_id=activo.pk
        )

    return ClienteNuevo(
        empresa=empresa,
        administrador=cuenta,
        membresia=membresia,
        rol=rol,
        password_temporal=temporal,
    )


__all__ = [
    "dar_de_alta",
    "DatosDelCliente",
    "DatosDelAdministrador",
    "ClienteNuevo",
    "NOMBRE_DEL_ROL_INICIAL",
]
