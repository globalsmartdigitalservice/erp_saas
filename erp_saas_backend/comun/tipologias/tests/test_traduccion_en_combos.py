import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from comun.idiomas import api as idiomas
from comun.tipologias.constantes import AGRUPADOR
from comun.tipologias.models import Tipologia
from config.schema import schema
from core.idioma import idioma
from core.tenancy import empresa, sin_filtro_de_empresa

pytestmark = pytest.mark.django_db

TABLA = Tipologia._meta.db_table

QUERY = "query ($ag: Int!) { tipologias(agrupador: $ag) { nombre } }"


@pytest.fixture
def ingles(db):
    from comun.idiomas import api as _idiomas

    return _idiomas.crear_idioma(codigo="en", nombre="Inglés")


def _nombres(agrupador=AGRUPADOR.RUBRO):
    resultado = schema.execute_sync(
        QUERY, variable_values={"ag": int(agrupador)}
    )
    assert resultado.errors is None, resultado.errors
    return [fila["nombre"] for fila in resultado.data["tipologias"]]


def _traducir_de_fabrica(fila, idioma_id, texto, campo="nombre"):
    with sin_filtro_de_empresa():
        return idiomas.guardar_traduccion_de_fabrica(
            entidad_tipo=TABLA,
            entidad_id=fila.pk,
            campo=campo,
            idioma_id=idioma_id,
            texto=texto,
        )


def test_el_combo_sale_en_el_idioma_activo(empresa_a, rubro_del_sistema, ingles):
    _traducir_de_fabrica(rubro_del_sistema, ingles.pk, "Retail")

    with empresa(empresa_a.id), idioma(ingles.pk):
        assert _nombres() == ["Retail"]


def test_si_no_se_pide_idioma_manda_el_de_la_empresa(
    empresa_a, rubro_del_sistema, ingles
):
    _traducir_de_fabrica(rubro_del_sistema, ingles.pk, "Retail")

    with empresa(empresa_a.id):
        assert _nombres() == ["Comercio"]


def test_lo_que_no_esta_traducido_sale_en_su_idioma_original(
    empresa_a, rubro_del_sistema, rubro_de, ingles
):
    _traducir_de_fabrica(rubro_del_sistema, ingles.pk, "Retail")
    rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id), idioma(ingles.pk):
        assert _nombres() == ["Retail", "Farmacia"]


def test_el_idioma_sale_de_la_empresa_cuando_no_se_pide_ninguno(
    crear_empresa, catalogo, rubro_del_sistema, ingles
):
    _traducir_de_fabrica(rubro_del_sistema, ingles.pk, "Retail")

    la_empresa = crear_empresa("Inglesa S.A.")
    with sin_filtro_de_empresa():
        la_empresa.idioma_default = ingles
        la_empresa.save(update_fields=["idioma_default"])

    with empresa(la_empresa.id):
        assert _nombres() == ["Retail"]


def test_la_traduccion_de_la_empresa_le_gana_a_la_de_fabrica(
    empresa_a, rubro_del_sistema, ingles
):
    _traducir_de_fabrica(rubro_del_sistema, ingles.pk, "Retail")

    with empresa(empresa_a.id):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Trade",
        )

    with empresa(empresa_a.id), idioma(ingles.pk):
        assert _nombres() == ["Trade"]


def test_la_traduccion_de_otra_empresa_no_se_cuela(
    empresa_a, empresa_b, rubro_del_sistema, ingles
):
    with empresa(empresa_b.id):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Lo de B",
        )

    with empresa(empresa_a.id), idioma(ingles.pk):
        assert _nombres() == ["Comercio"]


def test_el_nombre_de_la_lista_tambien_se_traduce(catalogo, empresa_a, ingles):
    cabecera = catalogo["tipologia"](AGRUPADOR.RUBRO, "Rubros")
    with sin_filtro_de_empresa():
        cabecera.indice = 0
        cabecera.save(update_fields=["indice"])

    _traducir_de_fabrica(cabecera, ingles.pk, "Industries")

    with empresa(empresa_a.id), idioma(ingles.pk):
        resultado = schema.execute_sync("{ agrupadores { valor nombre } }")

    assert resultado.errors is None
    nombres = [
        fila["nombre"]
        for fila in resultado.data["agrupadores"]
        if fila["valor"] == int(AGRUPADOR.RUBRO)
    ]
    assert nombres == ["Industries"]


def test_traducir_no_agrega_una_consulta_por_fila(
    catalogo, empresa_a, rubro_de, ingles
):
    _traducir_de_fabrica(catalogo["rubro"], ingles.pk, "Retail")

    with empresa(empresa_a.id), idioma(ingles.pk):
        with CaptureQueriesContext(connection) as uno:
            assert len(_nombres()) == 1

    for i in range(4):
        rubro_de(empresa_a, f"Rubro {i}")

    with empresa(empresa_a.id), idioma(ingles.pk):
        with CaptureQueriesContext(connection) as cinco:
            assert len(_nombres()) == 5

    assert len(uno) == len(cinco)


def test_sin_idioma_activo_no_se_consulta_traduccion(rubro_del_sistema):
    with idioma(None), CaptureQueriesContext(connection) as consultas:
        assert _nombres() == ["Comercio"]

    sql = " ".join(c["sql"] for c in consultas.captured_queries)
    assert "idio_traduccion" not in sql
