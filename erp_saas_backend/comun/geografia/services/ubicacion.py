from django.core.exceptions import ValidationError
from django.db import transaction

from comun.geografia.models import UbicacionGeografica
from comun.geografia.repository import pais as repo_pais
from comun.geografia.repository import ubicacion as repo
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA



PROFUNDIDAD_MAXIMA = 50


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado de ubicación"
    )


def _obtener_padre(division_superior_id: int) -> UbicacionGeografica:
    padre = repo.obtener(division_superior_id)
    if padre is None:
        raise ValidationError(
            f"No existe la ubicación superior {division_superior_id}."
        )
    return padre


def _ancestros(ubicacion: UbicacionGeografica) -> list[int]:
    """Los ids de todos los ancestros, de abajo hacia arriba."""
    ids = []
    actual = ubicacion
    for _ in range(PROFUNDIDAD_MAXIMA):
        if actual.division_superior_id is None:
            break
        ids.append(actual.division_superior_id)
        actual = repo.obtener(actual.division_superior_id)
        if actual is None:
            break
    return ids


@transaction.atomic
def crear(
    *,
    pais_id: int,
    nombre: str,
    tipo: str,
    estado_id: int,
    division_superior_id: int | None = None,
    codigo: str = "",
) -> UbicacionGeografica:
    if repo_pais.obtener(pais_id) is None:
        raise ValidationError(f"No existe el país {pais_id}.")

    _validar_estado(estado_id)

    # INVARIANTE 2 y 3: el país lo dicta el padre, y el nivel se calcula.
    if division_superior_id is None:
        nivel = 1
    else:
        padre = _obtener_padre(division_superior_id)
        if padre.pais_id != pais_id:
            raise ValidationError(
                f"La ubicación superior '{padre.nombre}' pertenece a otro país. "
                f"Una división no puede colgar de una de otro país."
            )
        nivel = padre.nivel + 1

    return repo.crear(
        pais_id=pais_id,
        division_superior_id=division_superior_id,
        codigo=codigo,
        nombre=nombre,
        tipo=tipo,
        nivel=nivel,
        estado_id=estado_id,
    )


@transaction.atomic
def mover(ubicacion_id: int, nuevo_padre_id: int | None) -> UbicacionGeografica:
    """
    Cambia de quién cuelga una ubicación.

    Es la operación peligrosa de una tabla recursiva: mal hecha, arma un
    ciclo y cualquier recorrido de la jerarquía se cuelga para siempre.
    """
    ubicacion = repo.obtener(ubicacion_id)
    if ubicacion is None:
        raise ValidationError(f"No existe la ubicación {ubicacion_id}.")

    if nuevo_padre_id is None:
        return repo.actualizar(ubicacion, division_superior_id=None, nivel=1)

    if nuevo_padre_id == ubicacion_id:
        raise ValidationError("Una ubicación no puede colgar de sí misma.")

    padre = _obtener_padre(nuevo_padre_id)

    if padre.pais_id != ubicacion.pais_id:
        raise ValidationError(
            f"'{padre.nombre}' pertenece a otro país. Una división no puede "
            f"colgar de una de otro país."
        )

    # INVARIANTE 4: el nuevo padre no puede ser descendiente de esta
    # ubicación. Se comprueba subiendo desde el padre: si aparecemos
    # nosotros, el movimiento arma un ciclo.
    if ubicacion_id in _ancestros(padre):
        raise ValidationError(
            f"No se puede mover '{ubicacion.nombre}' dentro de '{padre.nombre}': "
            f"'{padre.nombre}' está por debajo suyo y se formaría un ciclo."
        )

    return repo.actualizar(
        ubicacion,
        division_superior_id=nuevo_padre_id,
        nivel=padre.nivel + 1,
    )


@transaction.atomic
def desactivar(ubicacion_id: int) -> UbicacionGeografica:
    """Soft delete — nada se borra físicamente."""
    ubicacion = repo.obtener(ubicacion_id)
    if ubicacion is None:
        raise ValidationError(f"No existe la ubicación {ubicacion_id}.")

    inactivo = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if inactivo is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Ejecute: python manage.py cargar_semillas"
        )

    return repo.actualizar(ubicacion, estado_id=inactivo.pk)
