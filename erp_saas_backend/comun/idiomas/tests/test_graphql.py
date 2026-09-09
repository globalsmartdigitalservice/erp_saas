import pytest

from config.schema import schema

pytestmark = pytest.mark.django_db


def test_query_idiomas(espanol, ingles):
    resultado = schema.execute_sync("{ idiomas { codigo nombre activo } }")

    assert resultado.errors is None
    assert resultado.data["idiomas"] == [
        {"codigo": "es", "nombre": "Español", "activo": True},
        {"codigo": "en", "nombre": "Inglés", "activo": True},
    ]


def test_query_idiomas_solo_activos(espanol, ingles):
    from comun.idiomas import api as idiomas

    idiomas.desactivar_idioma(ingles.pk)

    resultado = schema.execute_sync("{ idiomas(soloActivos: true) { codigo } }")

    assert resultado.errors is None
    assert resultado.data["idiomas"] == [{"codigo": "es"}]


def test_query_idioma_inexistente_devuelve_null():
    resultado = schema.execute_sync('{ idioma(id: "999") { codigo } }')

    assert resultado.errors is None
    assert resultado.data["idioma"] is None


def test_mutation_crear_idioma(db):
    consulta = """
        mutation {
          crearIdioma(datos: { codigo: "PT", nombre: "Portugués" })
          { id codigo nombre activo }
        }
    """
    resultado = schema.execute_sync(consulta)

    assert resultado.errors is None
    assert resultado.data["crearIdioma"]["codigo"] == "pt"


def test_mutation_con_codigo_invalido_devuelve_error_legible(db):
    consulta = """
        mutation {
          crearIdioma(datos: { codigo: "portugués", nombre: "Portugués" }) { id }
        }
    """
    resultado = schema.execute_sync(consulta)

    assert resultado.errors is not None
    assert "código de idioma" in resultado.errors[0].message


def test_mutation_desactivar_y_activar(espanol):
    apagar = """mutation ($id: ID!) { desactivarIdioma(id: $id) { activo } }"""
    prender = """mutation ($id: ID!) { activarIdioma(id: $id) { activo } }"""
    variables = {"id": str(espanol.pk)}

    assert schema.execute_sync(apagar, variable_values=variables).data[
        "desactivarIdioma"
    ] == {"activo": False}
    assert schema.execute_sync(prender, variable_values=variables).data[
        "activarIdioma"
    ] == {"activo": True}


def test_el_input_de_actualizar_no_expone_activo():
    campos = {
        campo.name
        for campo in schema.schema_converter.type_map[
            "ActualizarIdiomaInput"
        ].definition.fields
    }

    assert "activo" not in campos
