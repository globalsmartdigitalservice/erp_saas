"""Acceso a datos de `TipologiaOculta`."""

from comun.tipologias.models import Tipologia, TipologiaOculta
from core.tenancy import sin_filtro_de_empresa


def esta_oculta(empresa_id: int, tipologia_id: int) -> bool:
    return TipologiaOculta.objects.filter(
        empresa_id=empresa_id, tipologia_id=tipologia_id
    ).exists()


def ids_ocultos_de(empresa_id: int) -> list[int]:
    return list(
        TipologiaOculta.objects.filter(empresa_id=empresa_id).values_list(
            "tipologia_id", flat=True
        )
    )


def listar_tipologias_ocultas(empresa_id: int, agrupador: int | None = None):
    """
    Las tipologías que esta empresa tiene ocultas, como filas de
    `Tipologia`.

    Sin esto la pantalla de configuración no puede ofrecer "volver a
    mostrar": el manager las excluye justamente por estar ocultas, así
    que pedirlas por el camino normal devuelve vacío.

    Por eso —y solo por eso— usa `sin_filtro_de_empresa()`. No es un
    agujero: los ids salen de las filas de ESA empresa, o sea que no
    puede devolver nada que ella no haya ocultado ella misma.
    """
    ids = ids_ocultos_de(empresa_id)
    if not ids:
        return []

    with sin_filtro_de_empresa():
        qs = Tipologia.objects.filter(pk__in=ids)
        if agrupador is not None:
            qs = qs.filter(agrupador=agrupador)
        return list(qs)


def ocultar(empresa_id: int, tipologia_id: int) -> TipologiaOculta:
    """Idempotente: ocultar dos veces deja una sola fila."""
    fila, _ = TipologiaOculta.objects.get_or_create(
        empresa_id=empresa_id, tipologia_id=tipologia_id
    )
    return fila


def mostrar(empresa_id: int, tipologia_id: int) -> int:
    """
    Borra la fila de verdad. Es la misma excepción al soft delete que
    `empresa_agrupador`: esto no es un dato del negocio, es una
    excepción de pantalla, y su AUSENCIA ya significa "se ve".
    """
    borradas, _ = TipologiaOculta.objects.filter(
        empresa_id=empresa_id, tipologia_id=tipologia_id
    ).delete()
    return borradas
