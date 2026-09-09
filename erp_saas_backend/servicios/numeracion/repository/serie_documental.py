"""Acceso a datos de `Serie_Documental`. Filtrado por empresa (tenant)."""

from servicios.numeracion.models import SerieDocumental


def obtener(serie_id: int) -> SerieDocumental | None:
    return SerieDocumental.objects.filter(pk=serie_id).first()


def obtener_varias(serie_ids) -> dict[int, SerieDocumental]:
    return {s.pk: s for s in SerieDocumental.objects.filter(pk__in=list(serie_ids))}


def listar() -> list[SerieDocumental]:
    return list(SerieDocumental.objects.all())


def listar_de_tipo(tipo_documento_id: int) -> list[SerieDocumental]:
    return list(SerieDocumental.objects.filter(tipo_documento_id=tipo_documento_id))


def existe(tipo_documento_id: int, prefijo: str, excluir_id: int | None = None) -> bool:
    qs = SerieDocumental.objects.filter(
        tipo_documento_id=tipo_documento_id, prefijo=prefijo
    )
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(**campos) -> SerieDocumental:
    return SerieDocumental.objects.create(**campos)


def actualizar(serie: SerieDocumental, **campos) -> SerieDocumental:
    for campo, valor in campos.items():
        setattr(serie, campo, valor)
    serie.save(update_fields=list(campos))
    return serie
