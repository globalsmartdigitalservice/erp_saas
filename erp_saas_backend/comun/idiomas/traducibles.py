"""El registro de lo que se puede traducir.

`Traduccion` apunta a cualquier fila de cualquier tabla con un par
(tabla, id): una FK polimórfica. Postgres no puede validar nada de eso
—`entidad_tipo` es texto—, así que un `"conf_tipologa"` con un typo entra
igual, la fila queda muerta y **no salta ningún error**: simplemente no
traduce nunca. Por eso el texto no es libre, se contrasta contra el
registro de este archivo.

Para agregar una tabla se suma su `db_table` con la tupla de campos. Va el
`db_table` REAL y no el nombre del modelo: es el mismo string que guarda
`Traduccion.entidad_tipo`.

QUÉ VA ACÁ Y QUÉ NO

Solo DATOS MAESTROS: los nombres y descripciones que el usuario ve en un
combo o en un título y están guardados en la base.

NO van los textos de la interfaz ("Guardar", "Razón social") —ésos son de
`Recurso_Texto`, otra tabla y otro mecanismo— ni los datos de una
transacción: el detalle de una factura no se traduce, se emitió como se
emitió.
"""

TRADUCIBLES: dict[str, tuple[str, ...]] = {
    # Módulo 14 — el catálogo que alimenta todos los combos del ERP.
    "conf_tipologia": ("nombre", "abreviatura"),
    # Módulo 04 — la segmentación comercial ("Mayorista", "VIP").
    "ent_categoria_entidad": ("nombre", "descripcion"),
}


def tablas() -> list[str]:
    """Las tablas traducibles, ordenadas. Lo consume el frontend."""
    return sorted(TRADUCIBLES)


def es_traducible(entidad_tipo: str) -> bool:
    return entidad_tipo in TRADUCIBLES


def campos_de(entidad_tipo: str) -> tuple[str, ...]:
    """Los campos traducibles de una tabla. Tupla vacía si no está."""
    return TRADUCIBLES.get(entidad_tipo, ())


__all__ = ["TRADUCIBLES", "tablas", "es_traducible", "campos_de"]
