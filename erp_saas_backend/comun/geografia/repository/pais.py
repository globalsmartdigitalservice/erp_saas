"""Acceso a datos de `Pais`."""

from comun.geografia.models import Pais


def obtener(pais_id: int) -> Pais | None:
    return Pais.objects.filter(pk=pais_id).first()


def obtener_varios(pais_ids) -> dict[int, Pais]:
    """
    Versión por lote. Obligatoria en todo lo que cruce una frontera
    de módulo: sin esto, cada resolver que resuelva
    el país de una lista reintroduce el N+1.
    """
    return {p.pk: p for p in Pais.objects.filter(pk__in=list(pais_ids))}


def listar() -> list[Pais]:
    return list(Pais.objects.all())


def existe_codigo_iso(codigo_iso: str, excluir_id: int | None = None) -> bool:
    qs = Pais.objects.filter(codigo_iso=codigo_iso)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def existe_cod_pais(cod_pais: str, excluir_id: int | None = None) -> bool:
    qs = Pais.objects.filter(cod_pais=cod_pais)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(*, cod_pais: str, nombre: str, codigo_iso: str, estado_id: int) -> Pais:
    return Pais.objects.create(
        cod_pais=cod_pais,
        nombre=nombre,
        codigo_iso=codigo_iso,
        estado_id=estado_id,
    )


def actualizar(pais: Pais, **campos) -> Pais:
    for campo, valor in campos.items():
        setattr(pais, campo, valor)
    pais.save(update_fields=list(campos))
    return pais
