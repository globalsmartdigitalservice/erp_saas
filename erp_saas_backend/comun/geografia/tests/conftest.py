import pytest

from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ESTADO_ACTIVO,
    NOMBRE_ESTADO_BAJA,
)
from comun.tipologias.models import Tipologia
from core.tenancy import sin_filtro_de_empresa


@pytest.fixture
def tipologia():
    """Fábrica: `tipologia(AGRUPADOR.ESTADO_REGISTRO, "Activo")`.

     El `indice` arranca en 1 y nunca es 0: el 0 es la CABECERA, la
    fila que guarda el NOMBRE de la lista, y ninguna consulta de valores
    la devuelve. Una tipología de prueba con índice 0 no
    aparecería en ningún combo y el test fallaría por el motivo
    equivocado.
    """

    contador = {"n": 0}

    def _crear(agrupador, nombre):
        contador["n"] += 1
        with sin_filtro_de_empresa():
            return Tipologia.objects.create(
                empresa=None,
                agrupador=agrupador,
                nombre=nombre,
                indice=contador["n"],
            )

    return _crear


@pytest.fixture
def estado_activo(db, tipologia):
    """
    La fila "Activo" de la lista COMPARTIDA de estados.

    Antes había una por entidad —estado de país, de ubicación, de
    moneda—, todas con los mismos dos valores. Ahora es una sola fila y
    la usan las tres, así que crear dos acá reventaría la constraint
    (empresa, agrupador, nombre).
    """
    return tipologia(AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO)


@pytest.fixture
def estado_de_baja(db, tipologia):
    return tipologia(AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)


@pytest.fixture
def tipologia_de_otro_agrupador(db, tipologia):
    """Un rubro. Sirve para probar que no se cuela como estado."""
    return tipologia(AGRUPADOR.RUBRO, "Comercio")


@pytest.fixture
def bolivia(db, estado_activo):
    from comun.geografia import api as geografia

    return geografia.crear_pais(
        cod_pais="BO", nombre="Bolivia", codigo_iso="BOL", estado_id=estado_activo.pk
    )


@pytest.fixture
def argentina(db, estado_activo):
    from comun.geografia import api as geografia

    return geografia.crear_pais(
        cod_pais="AR", nombre="Argentina", codigo_iso="ARG", estado_id=estado_activo.pk
    )
