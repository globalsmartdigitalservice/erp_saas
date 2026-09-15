"""Darle permisos a alguien desde un test, por el camino real de un cliente.

No se toca `auth_permission` a mano: lo que decide es `Grupo_Empresa_Permiso`,
y ese es el camino que hay que ejercitar.
"""

from django.contrib.auth.models import Permission

from comun.membresias import api as membresias
from core.tenancy import empresa
from dominios.seguridad import api as seguridad
from dominios.seguridad.permisos import content_type_del_ancla


def darle_el_permiso(
    persona, empresa_id: int, estado_id: int, *codenames: str, nombre_rol: str = "Supervisor"
):
    """Un rol de esa empresa, con los permisos adentro, en su membresía."""
    permisos = [
        Permission.objects.get_or_create(
            content_type=content_type_del_ancla(),
            codename=codename,
            defaults={"name": codename},
        )[0]
        for codename in codenames
    ]

    with empresa(empresa_id):
        rol = seguridad.crear_rol(nombre=nombre_rol, estado_id=estado_id)
        for permiso in permisos:
            seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=permiso.id)
        seguridad.asignar_rol(
            membresia_id=membresias.membresia_de(persona.id).id,
            grupo_id=rol.id,
            estado_id=estado_id,
        )

    return permisos


__all__ = ["darle_el_permiso"]
