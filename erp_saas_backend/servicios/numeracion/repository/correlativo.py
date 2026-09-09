"""
Acceso a datos de `Correlativo`.

 TODO LO QUE SE ESCRIBE ACÁ PASA POR UN LOCK. Este archivo tiene una
función que bloquea filas de la base, y es la única del sistema que lo
hace hasta ahora. Ver `services/correlativo.py` para el porqué.
"""

from django.db import transaction

from servicios.numeracion.models import Correlativo


def asegurar_existe(serie_id: int, gestion: int) -> None:
    """
    Crea el contador en 0 si es la primera vez que se numera esa gestión.

    Va ANTES del lock y no dentro: `select_for_update()` no puede
    bloquear una fila que no existe todavía, así que si el primer
    documento del año llegara directo al lock, no habría nada que trabar.

    `get_or_create` es seguro ante la carrera de dos primeros documentos
    simultáneos: si el segundo pierde, Django atrapa el IntegrityError de
    la constraint única y vuelve a leer.
    """
    Correlativo.objects.get_or_create(
        serie_documental_id=serie_id,
        gestion=gestion,
        defaults={"ultimo_numero": 0},
    )


def bloquear(serie_id: int, gestion: int) -> Correlativo:
    """
    Trae la fila del contador CON LOCK EXCLUSIVO hasta el fin de la
    transacción.

    A partir de acá, cualquier otra transacción que pida el mismo
    correlativo espera. Es exactamente lo que se quiere: la numeración de
    una serie es, por definición, una fila de a uno.

     Tiene que llamarse dentro de un `atomic()`. Django revienta si no,
    y está bien que reviente: sin transacción el lock se soltaría al
    instante y no serviría de nada.
    """
    return (
        Correlativo.objects.select_for_update()
        .get(serie_documental_id=serie_id, gestion=gestion)
    )


def guardar(correlativo: Correlativo) -> Correlativo:
    correlativo.save(update_fields=["ultimo_numero"])
    return correlativo


def obtener_de(serie_id: int, gestion: int) -> Correlativo | None:
    """Lectura SIN lock. Para mostrar, nunca para numerar."""
    return Correlativo.objects.filter(
        serie_documental_id=serie_id, gestion=gestion
    ).first()


def listar_de_serie(serie_id: int) -> list[Correlativo]:
    return list(
        Correlativo.objects.filter(serie_documental_id=serie_id).order_by("-gestion")
    )
