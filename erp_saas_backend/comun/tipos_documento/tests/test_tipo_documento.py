import pytest
from django.core.exceptions import ValidationError

from comun.tipologias.constantes import AGRUPADOR
from comun.tipos_documento import api as tipos_documento
from core.tenancy import empresa

pytestmark = pytest.mark.django_db


def test_las_tres_banderas_se_guardan(empresa_a, catalogo):
    with empresa(empresa_a.id):
        factura = tipos_documento.crear(
            codigo="FAC",
            nombre="FACTURA",
            estado_id=catalogo["estado_activo"].pk,
            afecta_stock=True,
            genera_ingreso=True,
            es_venta=True,
        )
        proforma = tipos_documento.crear(
            codigo="PRO",
            nombre="PROFORMA",
            estado_id=catalogo["estado_activo"].pk,
        )

    assert (factura.afecta_stock, factura.genera_ingreso, factura.es_venta) == (
        True, True, True,
    )
    assert (proforma.afecta_stock, proforma.genera_ingreso, proforma.es_venta) == (
        False, False, False,
    )


def test_el_codigo_se_normaliza(empresa_a, catalogo):
    with empresa(empresa_a.id):
        fila = tipos_documento.crear(
            codigo="  fac  ", nombre="FACTURA", estado_id=catalogo["estado_activo"].pk
        )

    assert fila.codigo == "FAC"


def test_el_codigo_no_se_repite_dentro_de_la_empresa(empresa_a, catalogo):
    with empresa(empresa_a.id):
        tipos_documento.crear(
            codigo="FAC", nombre="FACTURA", estado_id=catalogo["estado_activo"].pk
        )

        with pytest.raises(ValidationError, match="FAC"):
            tipos_documento.crear(
                codigo="fac", nombre="OTRA", estado_id=catalogo["estado_activo"].pk
            )


def test_el_codigo_si_se_repite_entre_empresas(empresa_a, empresa_b, catalogo):
    with empresa(empresa_a.id):
        tipos_documento.crear(
            codigo="FAC", nombre="FACTURA", estado_id=catalogo["estado_activo"].pk
        )

    with empresa(empresa_b.id):
        otra = tipos_documento.crear(
            codigo="FAC", nombre="FACTURA", estado_id=catalogo["estado_activo"].pk
        )

    assert otra.pk is not None


def test_el_codigo_vacio_se_rechaza(empresa_a, catalogo):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="no puede ir vac"):
            tipos_documento.crear(
                codigo="   ", nombre="SIN CÓDIGO", estado_id=catalogo["estado_activo"].pk
            )


def test_un_estado_de_otra_lista_se_rechaza(empresa_a, catalogo):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Se esperaba un estado del registro"):
            tipos_documento.crear(
                codigo="X",
                nombre="X",
                estado_id=catalogo["tipologia"](AGRUPADOR.RUBRO, "UN RUBRO").pk,
            )


def test_el_de_otra_empresa_no_existe(empresa_a, empresa_b, catalogo):
    with empresa(empresa_a.id):
        fila = tipos_documento.crear(
            codigo="FAC", nombre="FACTURA", estado_id=catalogo["estado_activo"].pk
        )

    with empresa(empresa_b.id):
        assert tipos_documento.obtener(fila.pk) is None
        assert tipos_documento.listar() == []
