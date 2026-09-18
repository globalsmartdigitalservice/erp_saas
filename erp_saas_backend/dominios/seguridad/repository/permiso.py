"""Lectura del catálogo de permisos de negocio."""

from django.contrib.auth.models import Permission

from dominios.seguridad.permisos import content_type_del_ancla


def listar_catalogo() -> list[Permission]:
    """El ancla deja afuera los permisos internos de Django."""
    return list(
        Permission.objects.filter(content_type=content_type_del_ancla())
        .select_related("content_type")
        .order_by("codename")
    )
