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


AGREGAR_MONEDA = """
    mutation ($moneda: ID!) {
      agregarMonedaAEmpresa(monedaId: $moneda) { id esMonedaOficial }
    }
"""


def _monedas_de(empresa_id) -> set[int]:
    return {fila.moneda_id for fila in empresas.listar_monedas_de(empresa_id)}


@pytest.fixture
def dolar(catalogo_empresas):
    from comun.monedas import api as monedas

    return monedas.crear_moneda(
        descripcion="Dólar estadounidense",
        codigo="USD",
        estado_id=catalogo_empresas["estado_activo"].pk,
    )


def test_agregar_moneda_sin_sesion_no_escribe(matriz, dolar, catalogo_empresas):
    """Hasta el 2026-09-14 esta mutation no tenía ninguna guarda ni recibía
    `info`: le cambiaba las monedas a cualquier empresa del sistema, sin
    cookie y sin sesión. El test existe porque quitar el decorador no rompe
    nada más — la reapertura sería silenciosa."""
    from core.tests.contexto_graphql import Contexto
    from dominios.seguridad.permisos_graphql import SIN_SESION

    with empresa(matriz.pk):
        resultado = schema.execute_sync(
            AGREGAR_MONEDA,
            variable_values={"moneda": str(dolar.pk)},
            context_value=Contexto(None),
        )

    assert resultado.errors[0].message == SIN_SESION
    assert _monedas_de(matriz.pk) == {catalogo_empresas["moneda"].pk}


def test_la_moneda_se_agrega_a_la_empresa_de_la_sesion(
    matriz, otra_empresa, dolar, catalogo_empresas
):
    """La empresa sale del token, no del input. El caso permitido al lado del
    prohibido: agregar tiene que seguir funcionando, y tiene que escribir
    donde está parada la sesión."""
    from django.contrib.auth import get_user_model

    from core.tests.contexto_graphql import Contexto

    Usuario = get_user_model()
    # Del proveedor: pasa el guard por `is_superuser`. Acá se prueba EN QUÉ
    # empresa escribe, no quién puede — eso ya lo cubre `test_guards.py`.
    del_proveedor = Usuario.objects.create_superuser(
        username="carla", email="carla@acme.test", password="Kx7pLm9Qw2"
    )

    with empresa(matriz.pk):
        resultado = schema.execute_sync(
            AGREGAR_MONEDA,
            variable_values={"moneda": str(dolar.pk)},
            context_value=Contexto(del_proveedor),
        )

    assert resultado.errors is None
    assert dolar.pk in _monedas_de(matriz.pk)
    assert dolar.pk not in _monedas_de(otra_empresa.pk)


def test_agregar_moneda_ya_no_recibe_la_empresa():
    """Se mira el SDL y no el `type_map`: si el campo desapareciera o se
    renombrara, `next()` levanta y el test se pone en rojo. Buscando una clave
    en un diccionario, en cambio, pasaría sin haber probado nada."""
    firma = next(
        linea
        for linea in schema.as_str().splitlines()
        if "agregarMonedaAEmpresa(" in linea
    )

    assert "empresaId" not in firma


def test_el_input_no_expone_es_matriz():
    campos = {
        campo.name
        for campo in schema.schema_converter.type_map[
            "CrearEmpresaInput"
        ].definition.fields
    }

    assert "esMatriz" not in campos
    assert "es_matriz" not in campos
