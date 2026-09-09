"""Las consultas de idiomas."""

import strawberry

from comun.idiomas import api as idiomas
from core.tenancy import empresa_actual

from .types import IdiomaType, TablaTraducibleType, TraduccionType


@strawberry.type
class IdiomaQueries:
    @strawberry.field(
        description="Los idiomas del sistema. Con solo_activos = true "
        "devuelve los que se pueden elegir hoy."
    )
    def idiomas(self, solo_activos: bool = False) -> list[IdiomaType]:
        return [IdiomaType.desde_modelo(i) for i in idiomas.listar_idiomas(solo_activos)]

    @strawberry.field(description="Un idioma por su id.")
    def idioma(self, id: strawberry.ID) -> IdiomaType | None:
        fila = idiomas.obtener_idioma(int(id))
        return IdiomaType.desde_modelo(fila) if fila else None


@strawberry.type
class TraduccionQueries:
    @strawberry.field(
        description="Las traducciones de un registro, en todos los idiomas "
        "y campos. Es lo que llena el formulario de edición."
    )
    def traducciones_de(
        self, entidad_tipo: str, entidad_id: int
    ) -> list[TraduccionType]:
  
        empresa_id = empresa_actual()

        return [
            TraduccionType.desde_modelo(
                t,
          
                IdiomaType.desde_modelo(t.idioma),
                es_propia=t.empresa_id is not None and t.empresa_id == empresa_id,
            )
            for t in idiomas.listar_traducciones_de(entidad_tipo, entidad_id)
        ]

    @strawberry.field(
        description="Qué tablas se pueden traducir y qué campos de cada una. "
        "El frontend lo usa para saber dónde ofrecer los campos por idioma."
    )
    def tablas_traducibles(self) -> list[TablaTraducibleType]:
        return [
            TablaTraducibleType(tabla=tabla, campos=list(campos))
            for tabla, campos in sorted(idiomas.tablas_traducibles().items())
        ]


@strawberry.type
class IdiomaQuery(IdiomaQueries, TraduccionQueries):
    """La superficie de consulta de idiomas. Solo compone."""
