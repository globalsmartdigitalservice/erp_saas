"""Acceso a datos de `grupo_usuario` — quién tiene qué rol.

Es `ModeloTenantDerivado`, así que el filtro por empresa ya viene puesto
saltando a `usuario_empresa`.

 `roles_vigentes_de()` se llama en CADA verificación de permiso, así que
trae el rol y su empresa resueltos."""

import datetime

from django.db.models import Q

from dominios.seguridad.models import GrupoUsuario

_RELACIONES = ("grupo_empresa", "grupo_empresa__empresa", "usuario_empresa")


def obtener(asignacion_id: int) -> GrupoUsuario | None:
    return (
        GrupoUsuario.objects.select_related(*_RELACIONES)
        .filter(pk=asignacion_id)
        .first()
    )


def obtener_varias(asignacion_ids) -> dict[int, GrupoUsuario]:
    return {
        a.pk: a
        for a in GrupoUsuario.objects.select_related(*_RELACIONES).filter(
            pk__in=list(asignacion_ids)
        )
    }


def listar_de_membresia(membresia_id: int) -> list[GrupoUsuario]:
    """TODO el historial, vigentes y terminados: es la pantalla "¿quién le
    dio permiso de anular, y cuándo?"."""
    return list(
        GrupoUsuario.objects.select_related(*_RELACIONES).filter(
            usuario_empresa_id=membresia_id
        )
    )


def roles_vigentes_de(
    membresia_id: int, estado_id: int, hoy: datetime.date | None = None
) -> list[GrupoUsuario]:
    """Los roles que esa persona tiene HOY.

     Las cuatro condiciones son necesarias. Sin la de `fecha_fin`, un
    reemplazo "por vacaciones" que venció en marzo seguiría habilitando en
    septiembre."""
    return roles_vigentes_de_varias([membresia_id], estado_id, hoy)


def roles_vigentes_de_varias(
    membresia_ids, estado_id: int, hoy: datetime.date | None = None
) -> list[GrupoUsuario]:
    return list(
        _vigentes(GrupoUsuario.objects.select_related(*_RELACIONES), estado_id, hoy)
        .filter(usuario_empresa_id__in=list(membresia_ids))
    )


def asignaciones_con_permiso(
    codename: str, estado_id: int, hoy: datetime.date | None = None
) -> list[tuple[int, int]]:
    """`(asignacion_id, membresia_id)` de quienes tienen ese permiso hoy en la
    empresa activa, con la membresía activa y la cuenta habilitada."""
    return list(
        _vigentes(GrupoUsuario.objects.all(), estado_id, hoy)
        .filter(
            usuario_empresa__estado_id=estado_id,
            usuario_empresa__usuario__is_active=True,
            grupo_empresa__permisos__auth_permission__codename=codename,
        )
        .values_list("pk", "usuario_empresa_id")
        .distinct()
    )


def hay_permanente_con_permiso(
    codename: str, estado_id: int, hoy: datetime.date | None = None
) -> bool:
    """Permanente es la asignación sin fecha de fin: la que no se vence sola."""
    return (
        _vigentes(GrupoUsuario.objects.all(), estado_id, hoy)
        .filter(
            fecha_fin__isnull=True,
            usuario_empresa__estado_id=estado_id,
            usuario_empresa__usuario__is_active=True,
            grupo_empresa__permisos__auth_permission__codename=codename,
        )
        .exists()
    )


def _vigentes(qs, estado_id: int, hoy: datetime.date | None):
    """Vigente es la asignación y también su rol."""
    hoy = hoy or datetime.date.today()
    return qs.filter(
        estado_id=estado_id,
        grupo_empresa__estado_id=estado_id,
        fecha_inicio__lte=hoy,
    ).filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy))


def listar_de_membresias(membresia_ids) -> list[GrupoUsuario]:
    """Los roles de VARIAS personas en UNA consulta: sin esta, una por
    persona."""
    return list(
        GrupoUsuario.objects.select_related(*_RELACIONES).filter(
            usuario_empresa_id__in=list(membresia_ids)
        )
    )


def hay_asignacion_vigente(
    membresia_id: int, grupo_id: int, excluir_id: int | None = None
) -> bool:
    """No se puede resolver con un `unique`: la tabla guarda historial, así
    que la misma pareja puede repetirse con fechas distintas. Lo que no puede
    haber es dos VIGENTES."""
    qs = GrupoUsuario.objects.filter(
        usuario_empresa_id=membresia_id,
        grupo_empresa_id=grupo_id,
        fecha_fin__isnull=True,
    )
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def hay_asignaciones_de_grupo(grupo_id: int) -> bool:
    """Para la baja del rol: si alguien lo tiene, no se da de baja solo."""
    return GrupoUsuario.objects.filter(
        grupo_empresa_id=grupo_id, fecha_fin__isnull=True
    ).exists()


def crear(**campos) -> GrupoUsuario:
    return GrupoUsuario.objects.create(**campos)


def actualizar(asignacion: GrupoUsuario, **campos) -> GrupoUsuario:
    for campo, valor in campos.items():
        setattr(asignacion, campo, valor)
    asignacion.save(update_fields=list(campos))
    return asignacion
