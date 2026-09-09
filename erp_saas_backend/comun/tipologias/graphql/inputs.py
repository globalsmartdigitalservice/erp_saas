"""Los inputs de las mutations de tipologías."""

import strawberry


@strawberry.input
class CrearTipologiaInput:
    agrupador: int
    nombre: str
    abreviatura: str = ""

    # Sin valor, el sistema lo manda al final de la lista. El 0 se
    # rechaza: es la cabecera, la fila que guarda el nombre de la lista.
    indice: int | None = None


@strawberry.input
class ActualizarTipologiaInput:
    nombre: str | None = None
    abreviatura: str | None = None
    indice: int | None = None
    # `agrupador` NO se puede cambiar: mover un valor de una lista a otra
    # deja huérfanas a todas las filas que ya lo apuntaban. Si hace falta,
    # se desactiva y se crea uno nuevo.
