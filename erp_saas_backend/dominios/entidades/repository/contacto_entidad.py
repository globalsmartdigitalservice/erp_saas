"""Acceso a datos de `Contacto_Entidad`. Filtrado por empresa (tenant)."""

from dominios.entidades.models import ContactoEntidad


def obtener(contacto_id: int) -> ContactoEntidad | None:
    return ContactoEntidad.objects.filter(pk=contacto_id).first()


def obtener_varios(contacto_ids) -> dict[int, ContactoEntidad]:
    return {
        c.pk: c for c in ContactoEntidad.objects.filter(pk__in=list(contacto_ids))
    }


def listar_de(entidad_id: int) -> list[ContactoEntidad]:
    return list(ContactoEntidad.objects.filter(entidad_id=entidad_id))


def crear(**campos) -> ContactoEntidad:
    return ContactoEntidad.objects.create(**campos)


def actualizar(contacto: ContactoEntidad, **campos) -> ContactoEntidad:
    for campo, valor in campos.items():
        setattr(contacto, campo, valor)
    contacto.save(update_fields=list(campos))
    return contacto
