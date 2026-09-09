"""Acceso a datos de `Rol_Entidad`. Filtrado por empresa (tenant)."""

from dominios.entidades.models import RolEntidad


def obtener(rol_id: int) -> RolEntidad | None:
    return RolEntidad.objects.filter(pk=rol_id).first()


def obtener_varios(rol_ids) -> dict[int, RolEntidad]:
    return {r.pk: r for r in RolEntidad.objects.filter(pk__in=list(rol_ids))}


def listar_de(entidad_id: int) -> list[RolEntidad]:
    return list(RolEntidad.objects.filter(entidad_id=entidad_id))


def listar_por_tipo(tipo_rol_id: int) -> list[RolEntidad]:
    """Los clientes, o los proveedores: la consulta que hace el negocio."""
    return list(RolEntidad.objects.filter(tipo_rol_id=tipo_rol_id))


def existe(entidad_id: int, tipo_rol_id: int, excluir_id: int | None = None) -> bool:
    qs = RolEntidad.objects.filter(entidad_id=entidad_id, tipo_rol_id=tipo_rol_id)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(**campos) -> RolEntidad:
    return RolEntidad.objects.create(**campos)


def actualizar(rol: RolEntidad, **campos) -> RolEntidad:
    for campo, valor in campos.items():
        setattr(rol, campo, valor)
    rol.save(update_fields=list(campos))
    return rol
