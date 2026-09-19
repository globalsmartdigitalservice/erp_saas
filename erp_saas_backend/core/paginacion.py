

from dataclasses import dataclass

from django.db.models import QuerySet


LIMITE_POR_DEFECTO = 25


LIMITE_MAXIMO = 100


VENTANA_MAXIMA = 10_000


class VentanaDemasiadoProfunda(ValueError):
    """
    Se pidió una página más allá de `VENTANA_MAXIMA`.

    Es un límite operativo del sistema, no un dato inválido del usuario:
    por eso no es un `ValidationError` de dominio.
    """


@dataclass(frozen=True)
class Pagina:
    """Un pedazo de una lista larga, más lo que la pantalla necesita."""

    items: list
    total: int
    limite: int
    desde: int

    @property
    def hay_siguiente(self) -> bool:
        return self.desde + self.limite < self.total


def limite_seguro(limite: int | None) -> int:
    """Acota lo que pidió el cliente a algo que el servidor aguanta."""
    if limite is None:
        return LIMITE_POR_DEFECTO
    return max(1, min(limite, LIMITE_MAXIMO))


def validar_ventana(desde: int, limite: int) -> None:
    if desde < 0:
        raise VentanaDemasiadoProfunda(
            "El desplazamiento no puede ser negativo."
        )

    if desde + limite > VENTANA_MAXIMA:
        raise VentanaDemasiadoProfunda(
            f"No se puede avanzar más allá de {VENTANA_MAXIMA:,} registros. "
            f"Use los filtros para acotar la búsqueda en vez de seguir "
            f"pasando páginas."
        )


def paginar(
    qs: QuerySet, *, orden: list[str], limite: int | None = None, desde: int = 0
) -> Pagina:
    """
    Corta un queryset y devuelve el pedazo con su total.

     `orden` ES OBLIGATORIO Y TIENE QUE TERMINAR EN UN CAMPO ÚNICO.

    Postgres, sin `ORDER BY`, devuelve las filas en el orden que se le
    canta. Paginado, eso significa que la misma fila puede salir en la
    página 1 y en la 2, y otra no salir nunca. **No falla, no da error:
    solo faltan datos.**

    Y el campo único al final tampoco sobra: si el orden es solo por
    nombre, dos personas que se llaman igual se siguen turnando entre
    páginas. El `pk` desempata.
    """
    limite = limite_seguro(limite)
    validar_ventana(desde, limite)

 
    total = qs.count()

    filas = list(qs.order_by(*orden)[desde : desde + limite])

    return Pagina(items=filas, total=total, limite=limite, desde=desde)


__all__ = [
    "Pagina",
    "paginar",
    "limite_seguro",
    "validar_ventana",
    "VentanaDemasiadoProfunda",
    "LIMITE_POR_DEFECTO",
    "LIMITE_MAXIMO",
    "VENTANA_MAXIMA",
]
