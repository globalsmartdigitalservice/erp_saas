import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from config.schema import schema

pytestmark = pytest.mark.django_db


def test_query_paises(bolivia):
    resultado = schema.execute_sync("{ paises { nombre codigoIso estado { nombre } } }")

    assert resultado.errors is None
    assert resultado.data["paises"] == [
        {"nombre": "Bolivia", "codigoIso": "BOL", "estado": {"nombre": "ACTIVO"}}
    ]


def test_query_pais_inexistente_devuelve_null():
    resultado = schema.execute_sync('{ pais(id: "999") { nombre } }')

    assert resultado.errors is None
    assert resultado.data["pais"] is None


def test_listar_paises_no_tiene_n_mas_1(estado_activo):
    from comun.geografia import api as geografia

    geografia.crear_pais(
        cod_pais="P1", nombre="Uno", codigo_iso="AAA", estado_id=estado_activo.pk
    )

    with CaptureQueriesContext(connection) as con_uno:
        schema.execute_sync("{ paises { nombre estado { nombre } } }")

    for i in range(2, 6):
        geografia.crear_pais(
            cod_pais=f"P{i}",
            nombre=f"Pais {i}",
            codigo_iso=f"{chr(64 + i)}{chr(64 + i)}{chr(64 + i)}",
            estado_id=estado_activo.pk,
        )

    with CaptureQueriesContext(connection) as con_cinco:
        schema.execute_sync("{ paises { nombre estado { nombre } } }")

    assert len(con_cinco) == len(con_uno)


def test_mutation_crear_pais(contexto_proveedor, estado_activo):
    consulta = """
        mutation ($estadoId: ID!) {
          crearPais(datos: {
            codPais: "AR", nombre: "Argentina", codigoIso: "ARG", estadoId: $estadoId
          }) { id nombre estado { nombre } }
        }
    """
    resultado = schema.execute_sync(
        consulta,
        variable_values={"estadoId": str(estado_activo.pk)},
        context_value=contexto_proveedor,
    )

    assert resultado.errors is None
    assert resultado.data["crearPais"]["nombre"] == "Argentina"
    assert resultado.data["crearPais"]["estado"]["nombre"] == "ACTIVO"


def test_mutation_con_estado_invalido_devuelve_error_legible(
    contexto_proveedor,
    tipologia_de_otro_agrupador,
):
    consulta = """
        mutation ($estadoId: ID!) {
          crearPais(datos: {
            codPais: "AR", nombre: "Argentina", codigoIso: "ARG", estadoId: $estadoId
          }) { id }
        }
    """
    resultado = schema.execute_sync(
        consulta,
        variable_values={"estadoId": str(tipologia_de_otro_agrupador.pk)},
        context_value=contexto_proveedor,
    )

    assert resultado.errors is not None
    assert "Se esperaba un estado de país" in resultado.errors[0].message


def test_mutation_desactivar_pais(contexto_proveedor, bolivia, estado_de_baja):
    consulta = """
        mutation ($id: ID!) {
          desactivarPais(id: $id) { estado { nombre } }
        }
    """
    resultado = schema.execute_sync(
        consulta,
        variable_values={"id": str(bolivia.pk)},
        context_value=contexto_proveedor,
    )

    assert resultado.errors is None
    assert resultado.data["desactivarPais"]["estado"]["nombre"] == "BAJA"


def test_el_input_de_ubicacion_no_expone_el_nivel():
    campos = {
        campo.name for campo in schema.schema_converter.type_map["CrearUbicacionInput"].definition.fields
    }

    assert "nivel" not in campos
