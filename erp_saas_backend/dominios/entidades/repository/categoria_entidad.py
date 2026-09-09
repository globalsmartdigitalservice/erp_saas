"""Acceso a datos de `Categoria_Entidad`. Filtrado por empresa (tenant)."""

from dominios.entidades.models import CategoriaEntidad


def obtener(categoria_id: int) -> CategoriaEntidad | None:
    return CategoriaEntidad.objects.filter(pk=categoria_id).first()


def obtener_varias(categoria_ids) -> dict[int, CategoriaEntidad]:
    return {
        c.pk: c
        for c in CategoriaEntidad.objects.filter(pk__in=list(categoria_ids))
    }


def listar() -> list[CategoriaEntidad]:
    return list(CategoriaEntidad.objects.all())


def existe_nombre(nombre: str, excluir_id: int | None = None) -> bool:
    qs = CategoriaEntidad.objects.filter(nombre=nombre)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(**campos) -> CategoriaEntidad:
    return CategoriaEntidad.objects.create(**campos)


def actualizar(categoria: CategoriaEntidad, **campos) -> CategoriaEntidad:
    for campo, valor in campos.items():
        setattr(categoria, campo, valor)
    categoria.save(update_fields=list(campos))
    return categoria
