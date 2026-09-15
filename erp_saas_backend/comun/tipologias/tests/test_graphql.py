import json

import pytest

from comun.tipologias.constantes import AGRUPADOR
from comun.tipologias.models import Tipologia
from config.schema import schema
from core.tenancy import empresa, sin_filtro_de_empresa

pytestmark = pytest.mark.django_db


def test_query_tipologias_de_una_lista(empresa_a, rubro_del_sistema, rubro_de):
    rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            "query ($ag: Int!) { tipologias(agrupador: $ag) { nombre esDelSistema } }",
            variable_values={"ag": int(AGRUPADOR.RUBRO)},
        )

    assert resultado.errors is None
    assert resultado.data["tipologias"] == [
        {"nombre": "Comercio", "esDelSistema": True},
        {"nombre": "Farmacia", "esDelSistema": False},
    ]


def test_query_agrupadores_saca_el_nombre_de_la_tabla():
    from django.core.management import call_command

    call_command("cargar_tipologias")

    resultado = schema.execute_sync("{ agrupadores { valor nombre } }")
    assert resultado.errors is None
    from comun.tipologias.management.commands.cargar_tipologias import CATALOGO

    nombre_lista, _ = CATALOGO[AGRUPADOR.RUBRO]

    assert {
        "valor": int(AGRUPADOR.RUBRO),
        "nombre": nombre_lista,
    } in resultado.data["agrupadores"]

    with sin_filtro_de_empresa():
        cabecera = Tipologia.objects.cabeceras().del_agrupador(AGRUPADOR.RUBRO).get()
        cabecera.nombre = "Giros comerciales"
        cabecera.save(update_fields=["nombre"])

    resultado = schema.execute_sync("{ agrupadores { valor nombre } }")
    assert {
        "valor": int(AGRUPADOR.RUBRO),
        "nombre": "Giros comerciales",
    } in resultado.data["agrupadores"]


def test_el_codigo_del_agrupador_no_cambia_aunque_se_renombre_la_lista():
    """El frontend pide cada combo por `codigo` porque las otras dos formas
    fallan EN SILENCIO: el `valor` se renumera y el `nombre` se traduce."""
    from django.core.management import call_command

    call_command("cargar_tipologias")

    consulta = "{ agrupadores { valor nombre codigo } }"

    antes = schema.execute_sync(consulta)
    assert antes.errors is None
    rubro_antes = next(
        a
        for a in antes.data["agrupadores"]
        if a["valor"] == int(AGRUPADOR.RUBRO)
    )
    assert rubro_antes["codigo"] == "RUBRO"

    with sin_filtro_de_empresa():
        cabecera = Tipologia.objects.cabeceras().del_agrupador(AGRUPADOR.RUBRO).get()
        cabecera.nombre = "Giros comerciales"
        cabecera.save(update_fields=["nombre"])

    despues = schema.execute_sync(consulta)
    rubro_despues = next(
        a
        for a in despues.data["agrupadores"]
        if a["valor"] == int(AGRUPADOR.RUBRO)
    )

    assert rubro_despues["nombre"] == "Giros comerciales", (
        "El nombre TIENE que cambiar: es un dato del proveedor."
    )
    assert rubro_despues["codigo"] == "RUBRO", (
        "El código NO puede cambiar: es la llave con la que el frontend "
        "pide esta lista. Si sale de la base, un renombre deja los combos "
        "vacíos sin dar ningún error."
    )


def test_todos_los_agrupadores_tienen_codigo():
    """Un código vacío no rompe nada visible: el combo queda vacío y nadie
    se entera."""
    from django.core.management import call_command

    call_command("cargar_tipologias")

    resultado = schema.execute_sync("{ agrupadores { valor codigo } }")

    assert resultado.errors is None
    sin_codigo = [a for a in resultado.data["agrupadores"] if not a["codigo"]]
    assert sin_codigo == [], (
        f"Estas cabeceras apuntan a un agrupador que no está declarado en "
        f"constantes.py: {sin_codigo}"
    )


def test_sin_semilla_no_hay_agrupadores_que_mostrar():
    resultado = schema.execute_sync("{ agrupadores { valor nombre } }")

    assert resultado.errors is None
    assert resultado.data["agrupadores"] == []


def test_mutation_crear_usa_la_empresa_del_contexto(empresa_a, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    consulta = """
        mutation ($ag: Int!) {
          crearTipologia(datos: { agrupador: $ag, nombre: "Farmacia" }) {
            nombre esDelSistema activo
          }
        }
    """
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            consulta, variable_values={"ag": int(AGRUPADOR.RUBRO)}
        )

    assert resultado.errors is None
    assert resultado.data["crearTipologia"] == {
        "nombre": "Farmacia",
        "esDelSistema": False,
        "activo": True,
    }


def test_mutation_sin_empresa_da_error_legible():
    consulta = """
        mutation ($ag: Int!) {
          crearTipologia(datos: { agrupador: $ag, nombre: "Farmacia" }) { id }
        }
    """
    resultado = schema.execute_sync(
        consulta, variable_values={"ag": int(AGRUPADOR.RUBRO)}
    )

    assert resultado.errors is not None
    assert "No hay empresa en el contexto" in resultado.errors[0].message


def test_mutation_rechaza_editar_una_del_sistema(empresa_a, rubro_del_sistema):
    consulta = """
        mutation ($id: ID!) {
          actualizarTipologia(id: $id, datos: { nombre: "Robado" }) { nombre }
        }
    """
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            consulta, variable_values={"id": str(rubro_del_sistema.pk)}
        )

    assert resultado.errors is not None
    assert "catálogo del sistema" in resultado.errors[0].message


def _pedir(client, consulta, empresa_id=None):
    cabeceras = {}
    if empresa_id is not None:
        cabeceras["HTTP_X_EMPRESA_ID"] = str(empresa_id)

    response = client.post(
        "/graphql/",
        data=json.dumps({"query": consulta}),
        content_type="application/json",
        **cabeceras,
    )
    return response


def test_la_cabecera_fija_la_empresa(client, empresa_a, empresa_b, rubro_de):
    rubro_de(empresa_a, "Farmacia")
    rubro_de(empresa_b, "Ferretería")

    consulta = "{ tipologias(agrupador: %d) { nombre } }" % int(AGRUPADOR.RUBRO)

    de_a = _pedir(client, consulta, empresa_a.id).json()["data"]["tipologias"]
    de_b = _pedir(client, consulta, empresa_b.id).json()["data"]["tipologias"]

    assert {t["nombre"] for t in de_a} == {"Comercio", "Farmacia"}
    assert {t["nombre"] for t in de_b} == {"Comercio", "Ferretería"}


def test_sin_cabecera_solo_se_ven_las_del_sistema(client, empresa_a, rubro_de):
    rubro_de(empresa_a, "Farmacia")

    consulta = "{ tipologias(agrupador: %d) { nombre } }" % int(AGRUPADOR.RUBRO)
    datos = _pedir(client, consulta).json()["data"]["tipologias"]

    assert {t["nombre"] for t in datos} == {"Comercio"}


def test_una_cabecera_que_no_es_numero_se_rechaza(client):
    response = _pedir(client, "{ version }", empresa_id="siete")

    assert response.status_code == 400


def test_la_empresa_no_queda_pegada_entre_peticiones(client, empresa_a, rubro_de):
    rubro_de(empresa_a, "Farmacia")
    consulta = "{ tipologias(agrupador: %d) { nombre } }" % int(AGRUPADOR.RUBRO)

    _pedir(client, consulta, empresa_a.id)
    despues = _pedir(client, consulta).json()["data"]["tipologias"]

    assert {t["nombre"] for t in despues} == {"Comercio"}
