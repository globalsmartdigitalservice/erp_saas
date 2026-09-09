from comun.catalogo_modulos.models import Funcionalidad

# `auth_permission__content_type` NO es opcional: sin él, armar el código
# "app_label.codename" dispara una consulta POR FUNCIONALIDAD.
_RELACIONES = (
    "sub_modulo",
    "sub_modulo__modulo_sistema",
    "auth_permission",
    "auth_permission__content_type",
)


def obtener(funcionalidad_id: int) -> Funcionalidad | None:
    return (
        Funcionalidad.objects.select_related(*_RELACIONES)
        .filter(pk=funcionalidad_id)
        .first()
    )


def obtener_varias(funcionalidad_ids) -> dict[int, Funcionalidad]:
    return {
        f.pk: f
        for f in Funcionalidad.objects.select_related(*_RELACIONES).filter(
            pk__in=list(funcionalidad_ids)
        )
    }


def listar(estado_id: int | None = None) -> list[Funcionalidad]:
    qs = Funcionalidad.objects.select_related(*_RELACIONES)
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def listar_de_sub_modulo(
    sub_modulo_id: int, estado_id: int | None = None
) -> list[Funcionalidad]:
    qs = Funcionalidad.objects.select_related(*_RELACIONES).filter(
        sub_modulo_id=sub_modulo_id
    )
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def listar_de_sub_modulos(
    sub_modulo_ids, estado_id: int | None = None
) -> list[Funcionalidad]:
    qs = Funcionalidad.objects.select_related(*_RELACIONES).filter(
        sub_modulo_id__in=list(sub_modulo_ids)
    )
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def obtener_por_permiso(auth_permission_id: int) -> Funcionalidad | None:
    return (
        Funcionalidad.objects.select_related(*_RELACIONES)
        .filter(auth_permission_id=auth_permission_id)
        .first()
    )


def existe_permiso(auth_permission_id: int, excluir_id: int | None = None) -> bool:
    qs = Funcionalidad.objects.filter(auth_permission_id=auth_permission_id)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def existe_nombre_en_sub_modulo(
    sub_modulo_id: int, nombre: str, excluir_id: int | None = None
) -> bool:
    qs = Funcionalidad.objects.filter(sub_modulo_id=sub_modulo_id, nombre=nombre)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(**campos) -> Funcionalidad:
    return Funcionalidad.objects.create(**campos)


def actualizar(funcionalidad: Funcionalidad, **campos) -> Funcionalidad:
    for campo, valor in campos.items():
        setattr(funcionalidad, campo, valor)
    funcionalidad.save(update_fields=list(campos))
    return funcionalidad
