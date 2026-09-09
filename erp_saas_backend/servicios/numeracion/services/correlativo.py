from django.core.exceptions import ValidationError
from django.db import connection, transaction

from servicios.numeracion.repository import correlativo as repo
from servicios.numeracion.repository import serie_documental as repo_serie


LOCK_TIMEOUT = "3s"


def _limitar_la_espera() -> None:
    """
    `SET LOCAL` — vale solo dentro de esta transacción y se deshace sola
    al terminar. No toca la configuración del servidor ni afecta a otras
    consultas.
    """
    with connection.cursor() as cursor:
        cursor.execute(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'")


@transaction.atomic
def siguiente_numero(serie_id: int, gestion: int) -> int:
    """
    Devuelve el próximo número de la serie para esa gestión.

     SE LLAMA DENTRO DE LA TRANSACCIÓN DE QUIEN EMITE EL DOCUMENTO.

    Ése es todo el truco: el `@transaction.atomic` de acá se une a la
    transacción de afuera si ya hay una. Así, si la venta falla después
    de pedir el número, el contador vuelve atrás con ella y el número se
    reutiliza.

    Llamarla suelta —solo para "ver" el siguiente— CONSUME el número.
    Para mirar sin consumir está `numero_actual()`.
    """
    serie = repo_serie.obtener(serie_id)
    if serie is None:

        raise ValidationError(f"No existe la serie documental {serie_id}.")

    if gestion is None or int(gestion) < 1900:
        raise ValidationError(
            f"La gestión '{gestion}' no es un año válido. Es el año fiscal al "
            f"que pertenece el documento."
        )

    _limitar_la_espera()


    repo.asegurar_existe(serie_id, gestion)
    fila = repo.bloquear(serie_id, gestion)

    fila.ultimo_numero += 1
    repo.guardar(fila)

    return fila.ultimo_numero


def numero_actual(serie_id: int, gestion: int) -> int:
    """
    El último número entregado, SIN consumir ninguno y SIN bloquear.

    Para mostrar en pantalla. **Nunca para numerar**: entre esta lectura y
    tu `INSERT` puede haber pasado cualquier cosa.
    """
    fila = repo.obtener_de(serie_id, gestion)
    return fila.ultimo_numero if fila else 0


def formatear(serie_id: int, numero: int, ancho: int = 6) -> str:
    """
    El número como se imprime: `FAC-000123`.

    El ancho es de acá, no del modelo de datos: si algún día hay que
    configurarlo por serie, es una columna más en `Serie_Documental`.
    """
    serie = repo_serie.obtener(serie_id)
    if serie is None:
        raise ValidationError(f"No existe la serie documental {serie_id}.")

    cuerpo = str(numero).zfill(ancho)
    return f"{serie.prefijo}-{cuerpo}" if serie.prefijo else cuerpo
