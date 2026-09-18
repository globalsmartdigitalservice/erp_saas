"""Acceso a datos de `Grupo_Empresa` y `Grupo_Empresa_Permiso`.

Las dos tienen manager propio, así que el filtro ya viene puesto: acá no se
escribe ninguna condición de empresa.

Los listados traen `select_related` porque la pantalla de roles muestra
cada rol con su empresa dueña y su cantidad de permisos: sin eso, 20 roles
son 41 consultas."""

from django.db.models import Count

from dominios.seguridad.models import GrupoEmpresa, GrupoEmpresaPermiso


def obtener(grupo_id: int) -> GrupoEmpresa | None:
    return GrupoEmpresa.objects.select_related("empresa").filter(pk=grupo_id).first()


def obtener_varios(grupo_ids) -> dict[int, GrupoEmpresa]:
    return {
        g.pk: g
        for g in GrupoEmpresa.objects.select_related("empresa").filter(
            pk__in=list(grupo_ids)
        )
    }


def listar(estado_id: int | None = None) -> list[GrupoEmpresa]:
    """`empresa` viene resuelta porque la pantalla marca cuáles son
    heredados —y por lo tanto no editables— sin una consulta por fila."""
    qs = GrupoEmpresa.objects.select_related("empresa")
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def listar_con_cantidad_de_permisos(
    estado_id: int | None = None,
) -> list[GrupoEmpresa]:
    """Cada rol trae `cantidad_permisos` ya contada: sin esto, mostrar
    "Cajero — 7 permisos" para 20 roles son 20 consultas más."""
    qs = GrupoEmpresa.objects.select_related("empresa").annotate(
        cantidad_permisos=Count("permisos")
    )
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def rol_homonimo_en_rama(
    nombre: str, excluir_id: int | None = None
) -> GrupoEmpresa | None:
    """El rol que ya usa ese nombre en la rama, o `None`.

    Es lo que el `unique(empresa, nombre)` no puede hacer: para Postgres el
    "Cajero" de la matriz y el de la sucursal son filas de empresas distintas
    y pasan las dos. Para el usuario es el mismo nombre repetido.

    Devuelve la fila y no un bool porque el mensaje de error cambia según de
    quién sea: de ella, de su matriz o de una sucursal suya."""
    qs = GrupoEmpresa.objects.de_rama().filter(nombre=nombre)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.select_related("empresa").first()


def crear(**campos) -> GrupoEmpresa:
    return GrupoEmpresa.objects.create(**campos)


def actualizar(grupo: GrupoEmpresa, **campos) -> GrupoEmpresa:
    for campo, valor in campos.items():
        setattr(grupo, campo, valor)
    grupo.save(update_fields=list(campos))
    return grupo


# `content_type` va SIEMPRE con el permiso: sin él, armar el código
# "app_label.codename" dispara una consulta POR PERMISO, en cada request.
_RELACIONES = ("auth_permission", "auth_permission__content_type")


def listar_permisos_de(grupo_id: int) -> list[GrupoEmpresaPermiso]:
    return list(
        GrupoEmpresaPermiso.objects.select_related(*_RELACIONES).filter(
            grupo_empresa_id=grupo_id
        )
    )


def listar_permisos_de_varios(grupo_ids) -> list[GrupoEmpresaPermiso]:
    """Los permisos de VARIOS roles en UNA consulta. La usa el backend de
    autenticación: sin esta, una consulta por rol en cada verificación de
    permiso."""
    return list(
        GrupoEmpresaPermiso.objects.select_related(*_RELACIONES).filter(
            grupo_empresa_id__in=list(grupo_ids)
        )
    )


def existe_permiso_en(grupo_id: int, auth_permission_id: int) -> bool:
    return GrupoEmpresaPermiso.objects.filter(
        grupo_empresa_id=grupo_id, auth_permission_id=auth_permission_id
    ).exists()


def agregar_permiso(grupo_id: int, auth_permission_id: int) -> GrupoEmpresaPermiso:
    return GrupoEmpresaPermiso.objects.create(
        grupo_empresa_id=grupo_id, auth_permission_id=auth_permission_id
    )


def quitar_permiso(grupo_id: int, auth_permission_id: int) -> int:
    borradas, _ = GrupoEmpresaPermiso.objects.filter(
        grupo_empresa_id=grupo_id, auth_permission_id=auth_permission_id
    ).delete()
    return borradas
