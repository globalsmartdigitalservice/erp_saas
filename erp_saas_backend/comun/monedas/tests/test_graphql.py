import decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from comun.monedas import api as monedas
from config.schema import schema
from core.tenancy import empresa

from .conftest import DOMINGO, VIERNES

pytestmark = pytest.mark.django_db


def test_query_monedas(boliviano, dolar):
    resultado = schema.execute_sync(
        "{ monedas { codigo simbolo estado { nombre } } }"
    )

    assert resultado.errors is None
    assert resultado.data["monedas"] == [
        {"codigo": "BOB", "simbolo": "Bs", "estado": {"nombre": "ACTIVO"}},
        {"codigo": "USD", "simbolo": "$", "estado": {"nombre": "ACTIVO"}},
    ]


def test_query_moneda_inexistente_devuelve_null():
    resultado = schema.execute_sync('{ moneda(id: "999") { codigo } }')

    assert resultado.errors is None
    assert resultado.data["moneda"] is None


def test_ya_no_existe_la_query_moneda_oficial():
    resultado = schema.execute_sync("{ monedaOficial { codigo } }")

    assert resultado.errors is not None


def test_listar_monedas_no_tiene_n_mas_1(estado_activo):
    monedas.crear_moneda(
        descripcion="Uno", codigo="AAA", estado_id=estado_activo.pk
    )

    with CaptureQueriesContext(connection) as con_una:
        schema.execute_sync("{ monedas { codigo estado { nombre } } }")

    for codigo in ("BBB", "CCC", "DDD", "EEE"):
        monedas.crear_moneda(
            descripcion=codigo, codigo=codigo, estado_id=estado_activo.pk
        )

    with CaptureQueriesContext(connection) as con_cinco:
        schema.execute_sync("{ monedas { codigo estado { nombre } } }")

    assert len(con_cinco) == len(con_una)


def test_query_cotizacion_devuelve_la_vigente(empresa_a, dolar, boliviano):
    consulta = """
        query ($origen: ID!, $destino: ID!, $fecha: Date!) {
          cotizacion(
            monedaOrigenId: $origen, monedaDestinoId: $destino, fecha: $fecha
          ) { fecha valor }
        }
    """
    with empresa(empresa_a.id):
        monedas.registrar_cotizacion(
            moneda_origen_id=dolar.pk,
            moneda_destino_id=boliviano.pk,
            fecha=VIERNES,
            valor=decimal.Decimal("6.96"),
        )
        resultado = schema.execute_sync(
            consulta,
            variable_values={
                "origen": str(dolar.pk),
                "destino": str(boliviano.pk),
                "fecha": DOMINGO.isoformat(),
            },
        )

    assert resultado.errors is None
    assert resultado.data["cotizacion"]["fecha"] == VIERNES.isoformat()


def test_mutation_crear_moneda(estado_activo):
    consulta = """
        mutation ($estadoId: ID!) {
          crearMoneda(datos: {
            descripcion: "Sol peruano", codigo: "PEN", simbolo: "S/",
            estadoId: $estadoId
          }) { id codigo estado { nombre } }
        }
    """
    resultado = schema.execute_sync(
        consulta, variable_values={"estadoId": str(estado_activo.pk)}
    )

    assert resultado.errors is None
    assert resultado.data["crearMoneda"]["codigo"] == "PEN"
    assert resultado.data["crearMoneda"]["estado"]["nombre"] == "ACTIVO"


def test_mutation_con_estado_invalido_devuelve_error_legible(
    tipologia_de_otro_agrupador,
):
    consulta = """
        mutation ($estadoId: ID!) {
          crearMoneda(datos: {
            descripcion: "Sol", codigo: "PEN", estadoId: $estadoId
          }) { id }
        }
    """
    resultado = schema.execute_sync(
        consulta, variable_values={"estadoId": str(tipologia_de_otro_agrupador.pk)}
    )

    assert resultado.errors is not None
    assert "Se esperaba un estado de moneda" in resultado.errors[0].message


def test_mutation_registrar_cotizacion(empresa_a, dolar, boliviano):
    consulta = """
        mutation ($origen: ID!, $destino: ID!, $fecha: Date!) {
          registrarCotizacion(datos: {
            monedaOrigenId: $origen, monedaDestinoId: $destino,
            fecha: $fecha, valor: "6.96"
          }) { valor monedaOrigenId monedaDestinoId }
        }
    """
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            consulta,
            variable_values={
                "origen": str(dolar.pk),
                "destino": str(boliviano.pk),
                "fecha": VIERNES.isoformat(),
            },
        )

    assert resultado.errors is None
    assert resultado.data["registrarCotizacion"]["monedaOrigenId"] == str(dolar.pk)


def test_mutation_cotizar_una_moneda_contra_si_misma_da_error_legible(
    empresa_a, boliviano
):
    consulta = """
        mutation ($moneda: ID!, $fecha: Date!) {
          registrarCotizacion(datos: {
            monedaOrigenId: $moneda, monedaDestinoId: $moneda,
            fecha: $fecha, valor: "6.96"
          }) { id }
        }
    """
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            consulta,
            variable_values={
                "moneda": str(boliviano.pk),
                "fecha": VIERNES.isoformat(),
            },
        )

    assert resultado.errors is not None
    assert "contra sí misma" in resultado.errors[0].message


def test_mutation_anular_cotizacion(empresa_a, dolar, boliviano, estado_de_baja):
    consulta = """
        mutation ($id: ID!) { anularCotizacion(id: $id) { id } }
    """
    with empresa(empresa_a.id):
        fila = monedas.registrar_cotizacion(
            moneda_origen_id=dolar.pk,
            moneda_destino_id=boliviano.pk,
            fecha=VIERNES,
            valor=decimal.Decimal("6.96"),
        )
        resultado = schema.execute_sync(
            consulta, variable_values={"id": str(fila.pk)}
        )

        assert resultado.errors is None
        assert (
            monedas.cotizacion(
                moneda_origen_id=dolar.pk,
                moneda_destino_id=boliviano.pk,
                fecha=VIERNES,
            )
            is None
        )


def test_mutation_desactivar_moneda(dolar, estado_de_baja):
    consulta = """
        mutation ($id: ID!) {
          desactivarMoneda(id: $id) { estado { nombre } }
        }
    """
    resultado = schema.execute_sync(consulta, variable_values={"id": str(dolar.pk)})

    assert resultado.errors is None
    assert resultado.data["desactivarMoneda"]["estado"]["nombre"] == "BAJA"
