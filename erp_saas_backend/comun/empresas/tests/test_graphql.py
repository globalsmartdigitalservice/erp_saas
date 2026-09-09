import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from comun.empresas import api as empresas
from config.schema import schema

pytestmark = pytest.mark.django_db


def test_query_empresas(matriz):
    resultado = schema.execute_sync(
        "{ empresas { razonSocial esMatriz rubro { nombre } estado { nombre } } }"
    )

    assert resultado.errors is None
    assert resultado.data["empresas"] == [
        {
            "razonSocial": "Ferretería El Tornillo S.A.",
            "esMatriz": True,
            "rubro": {"nombre": "Comercio"},
            "estado": {"nombre": "ACTIVA"},
        }
    ]


def test_query_matrices_no_trae_sucursales(matriz, sucursal):
    resultado = schema.execute_sync("{ matrices { id } }")

    assert resultado.errors is None
    assert resultado.data["matrices"] == [{"id": str(matriz.pk)}]


def test_query_sucursales(matriz, sucursal):
    resultado = schema.execute_sync(
        'query ($id: ID!) { sucursales(empresaId: $id) { razonSocial } }',
        variable_values={"id": str(matriz.pk)},
    )

    assert resultado.errors is None
    assert len(resultado.data["sucursales"]) == 1


def test_listar_empresas_no_tiene_n_mas_1(matriz, datos_base):
    consulta = "{ empresas { razonSocial tipoEmpresa { nombre } rubro { nombre } estado { nombre } } }"

    with CaptureQueriesContext(connection) as con_una:
        schema.execute_sync(consulta)

    for n in range(2, 6):
        empresas.crear_empresa(
            ident_tributaria=f"NIT-{n}", razon_social=f"Empresa {n}", **datos_base
        )

    with CaptureQueriesContext(connection) as con_cinco:
        schema.execute_sync(consulta)

    assert len(con_cinco) == len(con_una)


def test_mutation_crear_empresa(datos_base, catalogo_empresas):
    consulta = """
        mutation ($tipo: ID!, $rubro: ID!, $estado: ID!, $idioma: ID!,
                  $moneda: ID!, $pais: ID!) {
          crearEmpresa(datos: {
            identTributaria: "555", razonSocial: "Nueva S.A.",
            tipoEmpresaId: $tipo, rubroId: $rubro, estadoId: $estado,
            idiomaDefaultId: $idioma, monedaOficialId: $moneda, paisId: $pais
          }) { id razonSocial esMatriz }
        }
    """
    resultado = schema.execute_sync(
        consulta,
        variable_values={
            "tipo": str(datos_base["tipo_empresa_id"]),
            "rubro": str(datos_base["rubro_id"]),
            "estado": str(datos_base["estado_id"]),
            "idioma": str(datos_base["idioma_default_id"]),
            "moneda": str(datos_base["moneda_oficial_id"]),
            "pais": str(datos_base["pais_id"]),
        },
    )

    assert resultado.errors is None
    assert resultado.data["crearEmpresa"]["esMatriz"] is True


def test_mutation_con_rubro_invalido_devuelve_error_legible(
    datos_base, catalogo_empresas
):
    consulta = """
        mutation ($tipo: ID!, $rubro: ID!, $estado: ID!, $idioma: ID!,
                  $moneda: ID!, $pais: ID!) {
          crearEmpresa(datos: {
            identTributaria: "556", razonSocial: "Mala S.A.",
            tipoEmpresaId: $tipo, rubroId: $rubro, estadoId: $estado,
            idiomaDefaultId: $idioma, monedaOficialId: $moneda, paisId: $pais
          }) { id }
        }
    """
    resultado = schema.execute_sync(
        consulta,
        variable_values={
            "tipo": str(datos_base["tipo_empresa_id"]),
            "rubro": str(catalogo_empresas["activa"].pk),  # un estado, no un rubro
            "estado": str(datos_base["estado_id"]),
            "idioma": str(datos_base["idioma_default_id"]),
            "moneda": str(datos_base["moneda_oficial_id"]),
            "pais": str(datos_base["pais_id"]),
        },
    )

    assert resultado.errors is not None
    assert "Se esperaba un valor de 'rubro'" in resultado.errors[0].message


def test_el_input_no_expone_es_matriz():
    campos = {
        campo.name
        for campo in schema.schema_converter.type_map[
            "CrearEmpresaInput"
        ].definition.fields
    }

    assert "esMatriz" not in campos
    assert "es_matriz" not in campos
