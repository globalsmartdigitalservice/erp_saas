"""Acceso a datos de `Direccion`. Filtrado por empresa (tenant)."""

from dominios.entidades.models import Direccion


def obtener(direccion_id: int) -> Direccion | None:
    return Direccion.objects.filter(pk=direccion_id).first()


def obtener_varias(direccion_ids) -> dict[int, Direccion]:
    return {d.pk: d for d in Direccion.objects.filter(pk__in=list(direccion_ids))}


def listar_de(entidad_id: int) -> list[Direccion]:
    return list(Direccion.objects.filter(entidad_id=entidad_id))


def crear(**campos) -> Direccion:
    return Direccion.objects.create(**campos)


def actualizar(direccion: Direccion, **campos) -> Direccion:
    for campo, valor in campos.items():
        setattr(direccion, campo, valor)
    direccion.save(update_fields=list(campos))
    return direccion
