"""Acceso a datos de `Modulo_Sistema`. Catálogo del proveedor, sin filtro."""


from comun.catalogo_modulos.models import ModuloSistema


def obtener(modulo_id: int) -> ModuloSistema | None:
    return ModuloSistema.objects.filter(pk=modulo_id).first()


def obtener_varios(modulo_ids) -> dict[int, ModuloSistema]:
    return {m.pk: m for m in ModuloSistema.objects.filter(pk__in=list(modulo_ids))}


def obtener_por_codigo(codigo: str) -> ModuloSistema | None:
    return ModuloSistema.objects.filter(codigo=codigo).first()


def listar(solo_vendibles: bool = False) -> list[ModuloSistema]:
    qs = ModuloSistema.objects.all()
    if solo_vendibles:
        qs = qs.filter(es_vendible=True)
    return list(qs)


def existe_codigo(codigo: str, excluir_id: int | None = None) -> bool:
    qs = ModuloSistema.objects.filter(codigo=codigo)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(**campos) -> ModuloSistema:
    return ModuloSistema.objects.create(**campos)


def actualizar(modulo: ModuloSistema, **campos) -> ModuloSistema:
    for campo, valor in campos.items():
        setattr(modulo, campo, valor)
    modulo.save(update_fields=list(campos))
    return modulo
