"""Los tipos que ve el frontend. Sin lógica: solo forma."""

import strawberry

from comun.idiomas.models import Idioma, Traduccion


@strawberry.type(name="Idioma")
class IdiomaType:
    """
    No recibe nada "ya resuelto" como `PaisType` o `MonedaType`: la
    tabla `idioma` no tiene ninguna FK, así que acá no hay N+1 posible
    y no hace falta el batch a mano.
    """

    id: strawberry.ID
    codigo: str
    nombre: str
    activo: bool

    @classmethod
    def desde_modelo(cls, idioma: Idioma) -> "IdiomaType":
        return cls(
            id=strawberry.ID(str(idioma.pk)),
            codigo=idioma.codigo,
            nombre=idioma.nombre,
            activo=idioma.activo,
        )


@strawberry.type(name="Traduccion")
class TraduccionType:
    """
    El idioma viene RESUELTO por parámetro, no se busca acá: es la regla
    de la casa y lo que obliga al batch. El repository ya lo trae
    con `select_related`.

     NO expone `empresa`. Que un texto sea propio, heredado de la
    matriz o de fábrica es asunto del backend; al frontend le importa
    `es_propia`, que es lo único que cambia lo que puede hacer: solo
    las propias se borran.
    """

    id: strawberry.ID
    entidad_tipo: str
    entidad_id: int
    campo: str
    idioma: IdiomaType
    texto: str
    es_propia: bool

    @classmethod
    def desde_modelo(
        cls, traduccion: Traduccion, idioma: IdiomaType, es_propia: bool
    ) -> "TraduccionType":
        return cls(
            id=strawberry.ID(str(traduccion.pk)),
            entidad_tipo=traduccion.entidad_tipo,
            entidad_id=traduccion.entidad_id,
            campo=traduccion.campo,
            idioma=idioma,
            texto=traduccion.texto,
            es_propia=es_propia,
        )


@strawberry.type(name="TablaTraducible")
class TablaTraducibleType:
    """
    Una fila del registro de `traducibles.py`.

    El frontend la usa para saber en qué formularios tiene que ofrecer
    los campos por idioma, en vez de tener la lista escrita de su lado
    —que es la forma segura de que las dos se desincronicen—.
    """

    tabla: str
    campos: list[str]
