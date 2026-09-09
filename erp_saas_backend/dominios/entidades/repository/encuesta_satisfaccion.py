"""Acceso a datos de `Encuesta_Satisfaccion`. Filtrado por empresa (tenant)."""

from dominios.entidades.models import EncuestaSatisfaccion


def obtener(encuesta_id: int) -> EncuestaSatisfaccion | None:
    return EncuestaSatisfaccion.objects.filter(pk=encuesta_id).first()


def obtener_varias(encuesta_ids) -> dict[int, EncuestaSatisfaccion]:
    return {
        e.pk: e
        for e in EncuestaSatisfaccion.objects.filter(pk__in=list(encuesta_ids))
    }


def listar_de(entidad_id: int) -> list[EncuestaSatisfaccion]:
    return list(
        EncuestaSatisfaccion.objects.filter(entidad_id=entidad_id).order_by("-fecha")
    )


def crear(**campos) -> EncuestaSatisfaccion:
    return EncuestaSatisfaccion.objects.create(**campos)
