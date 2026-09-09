import decimal

import pytest
from django.core.exceptions import ValidationError

from comun.monedas import api as monedas
from core.tenancy import empresa

from .conftest import DOMINGO, LUNES, SABADO, VIERNES

pytestmark = pytest.mark.django_db

SEIS_NOVENTA_Y_SEIS = decimal.Decimal("6.96")


def _registrar(la_empresa, origen, destino, fecha, valor):
    with empresa(la_empresa.id):
        return monedas.registrar_cotizacion(
            moneda_origen_id=origen.pk,
            moneda_destino_id=destino.pk,
            fecha=fecha,
            valor=valor,
        )


def _vigente(la_empresa, origen, destino, fecha):
    with empresa(la_empresa.id):
        return monedas.cotizacion(
            moneda_origen_id=origen.pk, moneda_destino_id=destino.pk, fecha=fecha
        )


def test_dos_empresas_cotizan_DISTINTO_el_mismo_par_el_mismo_dia(
    empresa_a, empresa_b, dolar, boliviano
):
    _registrar(empresa_a, dolar, boliviano, VIERNES, decimal.Decimal("8.00"))
    _registrar(empresa_b, dolar, boliviano, VIERNES, decimal.Decimal("9.00"))

    assert _vigente(empresa_a, dolar, boliviano, VIERNES).valor == decimal.Decimal(
        "8.00"
    )
    assert _vigente(empresa_b, dolar, boliviano, VIERNES).valor == decimal.Decimal(
        "9.00"
    )


def test_la_misma_moneda_contra_DOS_destinos_el_mismo_dia(
    empresa_a, dolar, boliviano, euro
):
    _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)
    _registrar(empresa_a, dolar, euro, VIERNES, decimal.Decimal("0.92"))

    assert _vigente(empresa_a, dolar, boliviano, VIERNES).valor == SEIS_NOVENTA_Y_SEIS
    assert _vigente(empresa_a, dolar, euro, VIERNES).valor == decimal.Decimal("0.92")


def test_una_empresa_no_ve_las_cotizaciones_de_otra(
    empresa_a, empresa_b, dolar, boliviano
):
    _registrar(empresa_a, dolar, boliviano, VIERNES, decimal.Decimal("8.00"))

    assert _vigente(empresa_b, dolar, boliviano, VIERNES) is None


def test_registrar_guarda_la_empresa_del_contexto(empresa_a, dolar, boliviano):
    cotizacion = _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)

    assert cotizacion.empresa_id == empresa_a.id
    assert cotizacion.valor == SEIS_NOVENTA_Y_SEIS


def test_sin_empresa_en_el_contexto_no_se_puede_cargar(db, dolar, boliviano):
    with pytest.raises(ValidationError, match="No hay empresa en el contexto"):
        monedas.registrar_cotizacion(
            moneda_origen_id=dolar.pk,
            moneda_destino_id=boliviano.pk,
            fecha=VIERNES,
            valor=SEIS_NOVENTA_Y_SEIS,
        )


@pytest.mark.parametrize("valor", [decimal.Decimal("0"), decimal.Decimal("-1.5")])
def test_el_valor_tiene_que_ser_mayor_a_cero(valor, empresa_a, dolar, boliviano):
    with pytest.raises(ValidationError, match="mayor a cero"):
        _registrar(empresa_a, dolar, boliviano, VIERNES, valor)


def test_una_moneda_no_se_cotiza_contra_si_misma(empresa_a, boliviano):
    with pytest.raises(ValidationError, match="contra sí misma"):
        _registrar(empresa_a, boliviano, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)


def test_no_se_repite_el_par_y_la_fecha(empresa_a, dolar, boliviano):
    _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)

    with pytest.raises(ValidationError, match="Ya hay una cotización"):
        _registrar(empresa_a, dolar, boliviano, VIERNES, decimal.Decimal("6.97"))


def test_una_moneda_inexistente_da_error_legible(empresa_a, boliviano):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="No existe la moneda de origen"):
            monedas.registrar_cotizacion(
                moneda_origen_id=99999,
                moneda_destino_id=boliviano.pk,
                fecha=VIERNES,
                valor=SEIS_NOVENTA_Y_SEIS,
            )

        with pytest.raises(ValidationError, match="No existe la moneda de destino"):
            monedas.registrar_cotizacion(
                moneda_origen_id=boliviano.pk,
                moneda_destino_id=99999,
                fecha=VIERNES,
                valor=SEIS_NOVENTA_Y_SEIS,
            )


def test_el_domingo_devuelve_la_cotizacion_del_viernes(empresa_a, dolar, boliviano):
    viernes = _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)

    assert _vigente(empresa_a, dolar, boliviano, SABADO).pk == viernes.pk
    assert _vigente(empresa_a, dolar, boliviano, DOMINGO).pk == viernes.pk


def test_la_cotizacion_del_dia_le_gana_a_la_anterior(empresa_a, dolar, boliviano):
    _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)
    lunes = _registrar(empresa_a, dolar, boliviano, LUNES, decimal.Decimal("6.97"))

    assert _vigente(empresa_a, dolar, boliviano, LUNES).pk == lunes.pk


def test_no_devuelve_una_cotizacion_del_futuro(empresa_a, dolar, boliviano):
    _registrar(empresa_a, dolar, boliviano, LUNES, decimal.Decimal("6.97"))

    assert _vigente(empresa_a, dolar, boliviano, VIERNES) is None


def test_sin_ninguna_cotizacion_devuelve_none(empresa_a, dolar, boliviano):
    assert _vigente(empresa_a, dolar, boliviano, VIERNES) is None


def test_corregir_cambia_el_valor(empresa_a, dolar, boliviano):
    cotizacion = _registrar(
        empresa_a, dolar, boliviano, VIERNES, decimal.Decimal("69.6")
    )

    with empresa(empresa_a.id):
        corregida = monedas.corregir_cotizacion(cotizacion.pk, SEIS_NOVENTA_Y_SEIS)

    assert corregida.pk == cotizacion.pk
    assert corregida.valor == SEIS_NOVENTA_Y_SEIS


def test_corregir_tambien_valida_el_valor(empresa_a, dolar, boliviano):
    cotizacion = _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="mayor a cero"):
            monedas.corregir_cotizacion(cotizacion.pk, decimal.Decimal("0"))


def test_no_se_puede_corregir_la_de_otra_empresa(
    empresa_a, empresa_b, dolar, boliviano
):
    ajena = _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)

    with empresa(empresa_b.id):
        with pytest.raises(ValidationError, match="No existe la cotización"):
            monedas.corregir_cotizacion(ajena.pk, decimal.Decimal("7.00"))


def test_anular_la_saca_de_las_sugerencias(
    empresa_a, dolar, boliviano, estado_de_baja
):
    cotizacion = _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)

    with empresa(empresa_a.id):
        monedas.anular_cotizacion(cotizacion.pk)

    assert _vigente(empresa_a, dolar, boliviano, VIERNES) is None


def test_anular_NO_borra_la_fila(empresa_a, dolar, boliviano, estado_de_baja):
    cotizacion = _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)

    with empresa(empresa_a.id):
        monedas.anular_cotizacion(cotizacion.pk)

        assert monedas.obtener_cotizacion(cotizacion.pk) is not None


def test_una_anulada_sigue_ocupando_el_lugar(
    empresa_a, dolar, boliviano, estado_de_baja
):
    cotizacion = _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)

    with empresa(empresa_a.id):
        monedas.anular_cotizacion(cotizacion.pk)

    with pytest.raises(ValidationError, match="Ya hay una cotización"):
        _registrar(empresa_a, dolar, boliviano, VIERNES, decimal.Decimal("7.00"))


def test_el_historial_viene_de_la_mas_nueva_a_la_mas_vieja(
    empresa_a, dolar, boliviano
):
    _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)
    _registrar(empresa_a, dolar, boliviano, LUNES, decimal.Decimal("6.97"))

    with empresa(empresa_a.id):
        fechas = [
            c.fecha
            for c in monedas.cotizaciones(
                moneda_origen_id=dolar.pk, moneda_destino_id=boliviano.pk
            )
        ]

    assert fechas == [LUNES, VIERNES]


def test_el_historial_esconde_las_anuladas_salvo_que_se_pidan(
    empresa_a, dolar, boliviano, estado_de_baja
):
    vieja = _registrar(empresa_a, dolar, boliviano, VIERNES, SEIS_NOVENTA_Y_SEIS)
    _registrar(empresa_a, dolar, boliviano, LUNES, decimal.Decimal("6.97"))

    with empresa(empresa_a.id):
        monedas.anular_cotizacion(vieja.pk)

        normal = monedas.cotizaciones(
            moneda_origen_id=dolar.pk, moneda_destino_id=boliviano.pk
        )
        con_anuladas = monedas.cotizaciones(
            moneda_origen_id=dolar.pk,
            moneda_destino_id=boliviano.pk,
            incluir_anuladas=True,
        )

    assert [c.fecha for c in normal] == [LUNES]
    assert [c.fecha for c in con_anuladas] == [LUNES, VIERNES]
