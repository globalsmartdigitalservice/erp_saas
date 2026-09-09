"""Los inputs de las mutations."""

import strawberry


@strawberry.input
class CrearIdiomaInput:
    codigo: str
    nombre: str
    activo: bool = True


@strawberry.input
class GuardarTraduccionInput:
    """
    Un upsert: si esa empresa ya tenía texto para ese campo y ese idioma,
    se pisa; si no, nace.

    No lleva `empresa_id` —la regla de arriba— y tampoco lleva un id de
    traducción: el que guarda dice QUÉ está traduciendo, no en qué fila
    de la tabla de traducciones va. Así el frontend no necesita saber si
    la fila ya existía.
    """

    entidad_tipo: str = strawberry.field(
        description="El nombre de la TABLA cuyo texto se traduce, tal cual "
        "está en la base: 'conf_tipologia', 'ent_categoria_entidad'. La lista "
        "completa sale de la query `tablasTraducibles`."
    )
    entidad_id: int = strawberry.field(
        description="El id de la FILA dentro de esa tabla. No es un id de "
        "la tabla Entidad: acá 'entidad' significa 'un registro cualquiera'. "
        "Con entidadTipo 'conf_tipologia', el 5 es la tipología 5."
    )
    campo: str = strawberry.field(
        description="Qué columna de esa fila se traduce: 'nombre', "
        "'descripcion'. Tiene que estar declarada como traducible."
    )
    idioma_id: strawberry.ID
    texto: str


@strawberry.input
class ActualizarIdiomaInput:
    codigo: str | None = None
    nombre: str | None = None
    # `activo` NO está y no va a estar: prender y apagar son
    # `activarIdioma` y `desactivarIdioma`. Que la intención quede en el
    # nombre de la mutation y no escondida en un campo más del input.
