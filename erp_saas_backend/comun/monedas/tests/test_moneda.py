import pytest
from django.core.exceptions import ValidationError

from comun.monedas import api as monedas

pytestmark = pytest.mark.django_db


def test_crear_moneda(estado_activo):
    moneda = monedas.crear_moneda(
        descripcion="Sol peruano",
        codigo="PEN",
        simbolo="S/",
        estado_id=estado_activo.pk,
    )

    assert moneda.pk is not None
    assert moneda.estado_id == estado_activo.pk


def test_el_estado_tiene_que_ser_del_agrupador_correcto(tipologia_de_otro_agrupador):
    with pytest.raises(ValidationError, match="Se esperaba un estado de moneda"):
        monedas.crear_moneda(
            descripcion="Sol peruano",
            codigo="PEN",
            estado_id=tipologia_de_otro_agrupador.pk,
        )


def test_no_se_repite_el_codigo(dolar, estado_activo):
    with pytest.raises(ValidationError, match="código 'USD'"):
        monedas.crear_moneda(
            descripcion="Otro dólar", codigo="USD", estado_id=estado_activo.pk
        )


def test_el_codigo_se_guarda_en_mayusculas(estado_activo):
    moneda = monedas.crear_moneda(
        descripcion="Dólar", codigo="  usd  ", estado_id=estado_activo.pk
    )

    assert moneda.codigo == "USD"


@pytest.mark.parametrize("codigo", ["US", "USDE", "US1", "U$D", ""])
def test_el_codigo_tiene_que_ser_tres_letras(codigo, estado_activo):
    with pytest.raises(ValidationError, match="letras"):
        monedas.crear_moneda(
            descripcion="Rara", codigo=codigo, estado_id=estado_activo.pk
        )


# ACÁ HABÍA CUATRO TESTS DE "LA MONEDA OFICIAL" Y SE MUDARON.
#
# Vigilaban que hubiera UNA sola oficial en todo el sistema y que no se
# pudiera desmarcar ni desactivar. El modelo de datos eliminó `Moneda.esMonedaOficial`
# porque ese invariante era falso en un SaaS: obliga a que todos los
# clientes de la instalación lleven sus libros en la misma moneda.
#
# No se perdieron: viven en `comun/empresas/tests/test_empresa_moneda.py`,
# ahora POR EMPRESA. Esta tabla volvió a ser un catálogo y no tiene nada
# que decir sobre quién la usa.


def test_no_se_saca_del_catalogo_una_moneda_en_uso(empresa_a, boliviano, estado_de_baja):
    with pytest.raises(ValidationError, match="la está usando alguna empresa"):
        monedas.desactivar_moneda(boliviano.pk)


def test_desactivar_es_soft_delete(dolar, estado_de_baja):
    monedas.desactivar_moneda(dolar.pk)

    moneda = monedas.obtener_moneda(dolar.pk)
    assert moneda is not None
    assert moneda.estado_id == estado_de_baja.pk


def test_desactivar_sin_la_semilla_avisa_que_falta(dolar):
    with pytest.raises(ValidationError, match="cargar_semillas"):
        monedas.desactivar_moneda(dolar.pk)


def test_obtener_por_codigo_no_distingue_mayusculas(dolar):
    assert monedas.obtener_por_codigo("usd").pk == dolar.pk


def test_actualizar_no_choca_consigo_mismo(dolar):
    moneda = monedas.actualizar_moneda(dolar.pk, descripcion="Dólar americano")

    assert moneda.descripcion == "Dólar americano"
    assert moneda.codigo == "USD"
