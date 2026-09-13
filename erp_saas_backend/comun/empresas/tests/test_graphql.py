import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from comun.empresas import api as empresas
from config.schema import schema
from core.tenancy import empresa

pytestmark = pytest.mark.django_db


def test_query_empresas(contexto_proveedor, matriz):
    resultado = schema.execute_sync(
        "{ empresas { razonSocial esMatriz rubro { nombre } estado { nombre } } }",
        context_value=contexto_proveedor,
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


def test_query_matrices_no_trae_sucursales(contexto_proveedor, matriz, sucursal):
    resultado = schema.execute_sync(
        "{ matrices { id } }", context_value=contexto_proveedor
    )

    assert resultado.errors is None
    assert resultado.data["matrices"] == [{"id": str(matriz.pk)}]


def test_query_sucursales(contexto_proveedor, matriz, sucursal):
    with empresa(matriz.pk):
        resultado = schema.execute_sync(
            'query ($id: ID!) { sucursales(empresaId: $id) { razonSocial } }',
            variable_values={"id": str(matriz.pk)},
            context_value=contexto_proveedor,
        )

    assert resultado.errors is None
    assert len(resultado.data["sucursales"]) == 1


def test_no_se_ven_las_sucursales_de_otro_cliente(
    contexto_proveedor, matriz, datos_base
):
    """El id llega por parámetro y `Empresa` no tiene filtro de tenancy:
    sin la comprobación del grupo, esto devuelve las del otro cliente."""
    otro_cliente = empresas.crear_empresa(
        ident_tributaria="NIT-OTRO", razon_social="Gimnasio S.R.L.", **datos_base
    )

    with empresa(matriz.pk):
        resultado = schema.execute_sync(
            'query ($id: ID!) { sucursales(empresaId: $id) { razonSocial } }',
            variable_values={"id": str(otro_cliente.pk)},
            context_value=contexto_proveedor,
        )

    # El mismo mensaje que si no existiera: no se confirma que ese id exista.
    assert f"No existe la empresa {otro_cliente.pk}" in resultado.errors[0].message


def test_listar_empresas_no_tiene_n_mas_1(contexto_proveedor, matriz, datos_base):
    consulta = "{ empresas { razonSocial tipoEmpresa { nombre } rubro { nombre } estado { nombre } } }"

    with CaptureQueriesContext(connection) as con_una:
        schema.execute_sync(consulta, context_value=contexto_proveedor)

    for n in range(2, 6):
        empresas.crear_empresa(
            ident_tributaria=f"NIT-{n}", razon_social=f"Empresa {n}", **datos_base
        )

    with CaptureQueriesContext(connection) as con_cinco:
        schema.execute_sync(consulta, context_value=contexto_proveedor)

    assert len(con_cinco) == len(con_una)


def test_mutation_crear_empresa(
    contexto_proveedor, datos_base, catalogo_empresas
):
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
        context_value=contexto_proveedor,
    )

    assert resultado.errors is None
    assert resultado.data["crearEmpresa"]["esMatriz"] is True


def test_mutation_con_rubro_invalido_devuelve_error_legible(
    contexto_proveedor, datos_base, catalogo_empresas
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
        context_value=contexto_proveedor,
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
