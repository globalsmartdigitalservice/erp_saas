"""Acceso a datos de `UbicacionGeografica`."""

from comun.geografia.models import UbicacionGeografica


def obtener(ubicacion_id: int) -> UbicacionGeografica | None:
    return UbicacionGeografica.objects.filter(pk=ubicacion_id).first()


def obtener_varias(ubicacion_ids) -> dict[int, UbicacionGeografica]:
    """Versión por lote — ver `repository/pais.obtener_varios`."""
    return {
        u.pk: u
        for u in UbicacionGeografica.objects.filter(pk__in=list(ubicacion_ids))
    }


def listar_de_pais(pais_id: int) -> list[UbicacionGeografica]:
    return list(UbicacionGeografica.objects.filter(pais_id=pais_id))


def listar_hijas(ubicacion_id: int) -> list[UbicacionGeografica]:
    """
    Solo las hijas DIRECTAS.

    Para "todos los municipios de Santa Cruz" hace falta una consulta
    recursiva (CTE), no este filtro.
    """
    return list(UbicacionGeografica.objects.filter(division_superior_id=ubicacion_id))


def listar_raices(pais_id: int) -> list[UbicacionGeografica]:
    return list(
        UbicacionGeografica.objects.filter(
            pais_id=pais_id, division_superior__isnull=True
        )
    )


def crear(
    *,
    pais_id: int,
    division_superior_id: int | None,
    codigo: str,
    nombre: str,
    tipo: str,
    nivel: int,
    estado_id: int,
) -> UbicacionGeografica:
    return UbicacionGeografica.objects.create(
        pais_id=pais_id,
        division_superior_id=division_superior_id,
        codigo=codigo,
        nombre=nombre,
        tipo=tipo,
        nivel=nivel,
        estado_id=estado_id,
    )


def actualizar(ubicacion: UbicacionGeografica, **campos) -> UbicacionGeografica:
    for campo, valor in campos.items():
        setattr(ubicacion, campo, valor)
    ubicacion.save(update_fields=list(campos))
    return ubicacion
