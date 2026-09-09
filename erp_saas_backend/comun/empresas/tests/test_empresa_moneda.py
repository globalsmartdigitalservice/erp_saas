import pytest
from django.core.exceptions import ValidationError

from comun.empresas import api as empresas
from comun.monedas import api as monedas
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA

pytestmark = pytest.mark.django_db


@pytest.fixture
def dolar(catalogo_empresas, estado_activo):
    return monedas.crear_moneda(
        descripcion="Dólar estadounidense",
        codigo="USD",
        simbolo="$",
        estado_id=estado_activo.pk,
    )


@pytest.fixture
def estado_activo(catalogo_empresas):
    """La misma fila "Activo" que ya usó el catálogo. No se crea otra."""
    return catalogo_empresas["estado_activo"]


@pytest.fixture
def estado_de_baja(catalogo_empresas, tipologia):
    """
    El otro valor de la lista compartida. El catálogo no lo trae, y hace
    falta para `quitar`: el soft delete apunta a esta fila.
    """
    return tipologia(AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)


def test_el_alta_crea_la_moneda_oficial(matriz, catalogo_empresas):
    oficial = empresas.moneda_oficial_de(matriz.pk)

    assert oficial is not None
    assert oficial.pk == catalogo_empresas["moneda"].pk


def test_la_empresa_arranca_operando_con_una_sola_moneda(matriz):
    filas = empresas.listar_monedas_de(matriz.pk)

    assert len(filas) == 1
    assert filas[0].es_moneda_oficial is True


def test_cada_empresa_tiene_LA_SUYA(matriz, sucursal, dolar):
    empresas.agregar_moneda(
        empresa_id=sucursal.pk, moneda_id=dolar.pk, es_moneda_oficial=True
    )

    assert empresas.moneda_oficial_de(matriz.pk).codigo == "BOB"
    assert empresas.moneda_oficial_de(sucursal.pk).codigo == "USD"


def test_marcar_una_oficial_desmarca_la_anterior(matriz, dolar):
    empresas.agregar_moneda(empresa_id=matriz.pk, moneda_id=dolar.pk)
    empresas.marcar_moneda_oficial(matriz.pk, dolar.pk)

    oficiales = [f for f in empresas.listar_monedas_de(matriz.pk) if f.es_moneda_oficial]

    assert len(oficiales) == 1
    assert empresas.moneda_oficial_de(matriz.pk).codigo == "USD"


def test_agregar_marcando_oficial_tambien_desmarca(matriz, dolar):
    empresas.agregar_moneda(
        empresa_id=matriz.pk, moneda_id=dolar.pk, es_moneda_oficial=True
    )

    oficiales = [f for f in empresas.listar_monedas_de(matriz.pk) if f.es_moneda_oficial]

    assert len(oficiales) == 1
    assert empresas.moneda_oficial_de(matriz.pk).codigo == "USD"


def test_desmarcar_una_empresa_no_toca_a_la_otra(matriz, sucursal, dolar):
    empresas.agregar_moneda(
        empresa_id=sucursal.pk, moneda_id=dolar.pk, es_moneda_oficial=True
    )

    assert empresas.moneda_oficial_de(matriz.pk).codigo == "BOB"


def test_marcar_la_que_ya_es_oficial_no_rompe(matriz, catalogo_empresas):
    fila = empresas.marcar_moneda_oficial(matriz.pk, catalogo_empresas["moneda"].pk)

    assert fila.es_moneda_oficial is True


def test_la_oficial_no_se_puede_quitar(matriz, catalogo_empresas):
    with pytest.raises(ValidationError, match="no se puede quitar"):
        empresas.quitar_moneda(matriz.pk, catalogo_empresas["moneda"].pk)


def test_una_que_no_es_oficial_si_se_puede_quitar(matriz, dolar, estado_de_baja):
    empresas.agregar_moneda(empresa_id=matriz.pk, moneda_id=dolar.pk)

    assert empresas.quitar_moneda(matriz.pk, dolar.pk) == 1


def test_quitar_es_soft_delete(matriz, dolar, estado_de_baja):
    empresas.agregar_moneda(empresa_id=matriz.pk, moneda_id=dolar.pk)
    empresas.quitar_moneda(matriz.pk, dolar.pk)

    codigos = [f.moneda_id for f in empresas.listar_monedas_de(matriz.pk)]

    assert dolar.pk in codigos


def test_no_se_repite_la_moneda_en_la_misma_empresa(matriz, catalogo_empresas):
    with pytest.raises(ValidationError, match="ya opera con"):
        empresas.agregar_moneda(
            empresa_id=matriz.pk, moneda_id=catalogo_empresas["moneda"].pk
        )


def test_una_moneda_inexistente_da_error_legible(matriz):
    with pytest.raises(ValidationError, match="No existe la moneda"):
        empresas.agregar_moneda(empresa_id=matriz.pk, moneda_id=99999)


def test_una_empresa_inexistente_da_error_legible(catalogo_empresas):
    with pytest.raises(ValidationError, match="No existe la empresa"):
        empresas.agregar_moneda(
            empresa_id=99999, moneda_id=catalogo_empresas["moneda"].pk
        )


def test_marcar_una_moneda_que_la_empresa_no_opera(matriz, dolar):
    with pytest.raises(ValidationError, match="no opera con"):
        empresas.marcar_moneda_oficial(matriz.pk, dolar.pk)


def test_saber_si_alguna_empresa_usa_una_moneda(matriz, dolar, catalogo_empresas):
    assert empresas.hay_empresas_con_moneda(catalogo_empresas["moneda"].pk) is True
    assert empresas.hay_empresas_con_moneda(dolar.pk) is False
