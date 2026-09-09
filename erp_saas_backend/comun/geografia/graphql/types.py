"""Los tipos que ve el frontend. Sin lógica: solo forma."""

import strawberry

from comun.geografia.models import Pais, UbicacionGeografica
from comun.tipologias.graphql.types import TipologiaType


@strawberry.type(name="Pais")
class PaisType:
    id: strawberry.ID
    cod_pais: str
    nombre: str
    codigo_iso: str


    estado: TipologiaType | None

    @classmethod
    def desde_modelo(cls, pais: Pais, estado: TipologiaType | None) -> "PaisType":
        return cls(
            id=strawberry.ID(str(pais.pk)),
            cod_pais=pais.cod_pais,
            nombre=pais.nombre,
            codigo_iso=pais.codigo_iso,
            estado=estado,
        )


@strawberry.type(name="UbicacionGeografica")
class UbicacionGeograficaType:
    id: strawberry.ID
    codigo: str
    nombre: str
    tipo: str
    nivel: int
    pais_id: strawberry.ID
    division_superior_id: strawberry.ID | None
    estado: TipologiaType | None

    @classmethod
    def desde_modelo(
        cls, ubicacion: UbicacionGeografica, estado: TipologiaType | None
    ) -> "UbicacionGeograficaType":
        padre = ubicacion.division_superior_id
        return cls(
            id=strawberry.ID(str(ubicacion.pk)),
            codigo=ubicacion.codigo,
            nombre=ubicacion.nombre,
            tipo=ubicacion.tipo,
            nivel=ubicacion.nivel,
            pais_id=strawberry.ID(str(ubicacion.pais_id)),
            division_superior_id=strawberry.ID(str(padre)) if padre else None,
            estado=estado,
        )
