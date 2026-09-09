from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas.models import EmpresaPais
from comun.empresas.repository import empresa as repo_empresa
from comun.empresas.repository import empresa_pais as repo
from comun.geografia import api as geografia


def _validar_pais(pais_id: int) -> None:
    if geografia.obtener_pais(pais_id) is None:
        raise ValidationError(f"No existe el país {pais_id}.")


def _validar_ubicacion(ubicacion_id: int | None, pais_id: int) -> None:
    """INVARIANTE 2 — la ubicación tiene que ser del país declarado."""
    if ubicacion_id is None:
        return

    ubicacion = geografia.obtener_ubicacion(ubicacion_id)
    if ubicacion is None:
        raise ValidationError(f"No existe la ubicación {ubicacion_id}.")

    if ubicacion.pais_id != pais_id:
        raise ValidationError(
            f"La ubicación '{ubicacion.nombre}' no pertenece a ese país. "
            f"La dirección quedaría apuntando a otro lado."
        )


@transaction.atomic
def agregar(
    *,
    empresa_id: int,
    pais_id: int,
    ubicacion_geografica_id: int | None = None,
    direccion: str = "",
    telefono: str = "",
    email: str = "",
    sitio_web: str = "",
    logo: str = "",
    latitud=None,
    longitud=None,
) -> EmpresaPais:
    if repo_empresa.obtener(empresa_id) is None:
        raise ValidationError(f"No existe la empresa {empresa_id}.")

    _validar_pais(pais_id)
    _validar_ubicacion(ubicacion_geografica_id, pais_id)

    if repo.existe(empresa_id, pais_id):
        raise ValidationError(
            "Esa empresa ya tiene una ficha para ese país. Si querés cambiar "
            "los datos de contacto, actualizá la que existe."
        )

    return repo.crear(
        empresa_id=empresa_id,
        pais_id=pais_id,
        ubicacion_geografica_id=ubicacion_geografica_id,
        direccion=direccion,
        telefono=telefono,
        email=email,
        sitio_web=sitio_web,
        logo=logo,
        latitud=latitud,
        longitud=longitud,
    )


@transaction.atomic
def actualizar(empresa_pais_id: int, **campos) -> EmpresaPais:
    """
    El `pais` NO se puede cambiar y no es parámetro: cambiarlo es, en
    los hechos, borrar la ficha de un país y crear la de otro. Que se
    haga explícito.
    """
    fila = repo.obtener(empresa_pais_id)
    if fila is None:
        raise ValidationError(f"No existe la ficha de país {empresa_pais_id}.")

    campos.pop("pais_id", None)
    campos.pop("empresa_id", None)

    if "ubicacion_geografica_id" in campos:
        _validar_ubicacion(campos["ubicacion_geografica_id"], fila.pais_id)

    campos = {c: v for c, v in campos.items() if v is not None}
    if not campos:
        return fila

    return repo.actualizar(fila, **campos)
