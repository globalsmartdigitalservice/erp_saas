import datetime

import pytest

from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA

# El viernes 28/08/2026. El 29 cae sábado y el 30 domingo: las fechas
# del ejemplo del fin de semana son reales, no inventadas.
VIERNES = datetime.date(2026, 8, 28)
SABADO = datetime.date(2026, 8, 29)
DOMINGO = datetime.date(2026, 8, 30)
LUNES = datetime.date(2026, 8, 31)


@pytest.fixture
def estado_activo(catalogo):
    """La fila "Activo" de la lista compartida de estados."""
    return catalogo["estado_activo"]


@pytest.fixture
def estado_de_baja(catalogo):
    """El otro valor de esa misma lista. El catálogo no lo trae."""
    return catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)


@pytest.fixture
def tipologia_de_otro_agrupador(catalogo):
    """Un rubro. Sirve para probar que no se cuela como estado."""
    return catalogo["rubro"]


@pytest.fixture
def boliviano(catalogo):
    """La moneda oficial del sistema. Es la del catálogo, no otra."""
    return catalogo["moneda"]


@pytest.fixture
def dolar(db, estado_activo):
    """Una moneda extranjera: es la que se cotiza."""
    from comun.monedas import api as monedas

    return monedas.crear_moneda(
        descripcion="Dólar estadounidense",
        codigo="USD",
        simbolo="$",
        estado_id=estado_activo.pk,
    )


@pytest.fixture
def euro(db, estado_activo):
    """Una tercera moneda, para probar pares que no son USD→BOB."""
    from comun.monedas import api as monedas

    return monedas.crear_moneda(
        descripcion="Euro",
        codigo="EUR",
        simbolo="€",
        estado_id=estado_activo.pk,
    )
