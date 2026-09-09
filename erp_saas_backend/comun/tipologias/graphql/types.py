"""El tipo `Tipologia` para el schema."""

import strawberry

from comun.tipologias.models import Tipologia
from core.tenancy import empresa_actual


@strawberry.type(name="Tipologia")
class TipologiaType:
    id: strawberry.ID
    agrupador: int
    indice: int
    nombre: str
    abreviatura: str

    # Qué botones mostrar. NO expone `empresa_id`: de qué empresa es una
    # fila ajena no es asunto de nadie.
    #
    #   es_del_sistema  →  de fábrica, la ven todos los clientes
    # es_propia         ÚNICO caso editable
    #
    # Hacen falta las dos: una heredada de la matriz no es del sistema y
    # tampoco es editable.
    es_del_sistema: bool
    es_propia: bool

    activo: bool

    @classmethod
    def desde_modelo(
        cls,
        tipologia: Tipologia,
        nombre: str | None = None,
        abreviatura: str | None = None,
    ) -> "TipologiaType":
        """
        `nombre` y `abreviatura` llegan TRADUCIDOS, o no llegan: el dato
        se pasa, no se busca. Quien arma la lista ya trajo todas las
        traducciones por lote, y acá no se consulta nada.

        None significa que no hay traducción en el idioma activo, y se
        muestra el texto original. Son opcionales para que las apps que
        todavía no traducen sigan llamando con un solo argumento.
        """
        return cls(
            id=strawberry.ID(str(tipologia.pk)),
            agrupador=tipologia.agrupador,
            indice=tipologia.indice,
            nombre=nombre if nombre is not None else tipologia.nombre,
            abreviatura=(
                abreviatura if abreviatura is not None else tipologia.abreviatura
            ),
            es_del_sistema=tipologia.empresa_id is None,
            es_propia=tipologia.empresa_id is not None
            and tipologia.empresa_id == empresa_actual(),
            activo=tipologia.estado == Tipologia.Estado.ACTIVO,
        )


@strawberry.type(name="Agrupador")
class AgrupadorType:
    """
    Una lista del sistema, para las pantallas de configuración.

        valor   5                   la POSICIÓN. Se renumera.
        nombre  "Tipos de entidad"  el CARTEL. Se edita y se traduce.
        codigo  TIPO_ENTIDAD        el nombre INTERNO. No cambia nunca.

     `codigo` es el único que sirve como llave, y por eso se expone. Un
    formulario que pide `tipologias(agrupador: N)` necesita saber la N, y
    las otras dos formas de averiguarla fallan **en silencio**: el `valor`
    se renumera —un 5 escrito en el frontend muestra la lista equivocada
    sin dar error— y el `nombre` lo cambia el proveedor y además se
    traduce, con lo que en inglés el combo queda vacío.
    """

    valor: int
    nombre: str
    codigo: str
