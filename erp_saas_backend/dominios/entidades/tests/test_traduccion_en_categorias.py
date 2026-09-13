import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from comun.idiomas import api as idiomas
from config.schema import schema
from core.idioma import idioma
from core.tenancy import empresa
from dominios.entidades.models import CategoriaEntidad

pytestmark = pytest.mark.django_db

TABLA = CategoriaEntidad._meta.db_table

QUERY = "{ categoriasEntidad { id nombre descripcion } }"


@pytest.fixture
def ingles(db):
    return idiomas.crear_idioma(codigo="en", nombre="Inglés")


@pytest.fixture
def categoria_de(catalogo_entidades):
    """Fábrica: `categoria_de(empresa_a, "Mayorista")`, ya en su contexto."""
    from dominios.entidades import api as entidades

    def _crear(la_empresa, nombre, descripcion=""):
        with empresa(la_empresa.id):
            return entidades.crear_categoria(
                nombre=nombre,
                descripcion=descripcion,
                estado_id=catalogo_entidades["estado_activo"].pk,
            )

    return _crear


def _categorias(contexto):
    resultado = schema.execute_sync(QUERY, context_value=contexto)
    assert resultado.errors is None, resultado.errors
    return [
        (fila["nombre"], fila["descripcion"])
        for fila in resultado.data["categoriasEntidad"]
    ]


def test_la_categoria_sale_en_el_idioma_activo(
    contexto_con_sesion, empresa_a, categoria_de, ingles
):
    categoria = categoria_de(empresa_a, "Mayorista", "Compra por volumen")

    with empresa(empresa_a.id):
        for campo, texto in (
            ("nombre", "Wholesale"),
            ("descripcion", "Buys in bulk"),
        ):
            idiomas.guardar_traduccion(
                entidad_tipo=TABLA,
                entidad_id=categoria.pk,
                campo=campo,
                idioma_id=ingles.pk,
                texto=texto,
            )

    with empresa(empresa_a.id), idioma(ingles.pk):
        assert _categorias(contexto_con_sesion) == [("Wholesale", "Buys in bulk")]


def test_lo_que_el_cliente_no_tradujo_sale_como_lo_cargo(
        contexto_con_sesion,
    empresa_a, categoria_de, ingles
):
    categoria_de(empresa_a, "Mayorista", "Compra por volumen")

    with empresa(empresa_a.id), idioma(ingles.pk):
        assert _categorias(contexto_con_sesion) == [("Mayorista", "Compra por volumen")]


def test_se_puede_traducir_solo_un_campo(
    contexto_con_sesion, empresa_a, categoria_de, ingles
):
    categoria = categoria_de(empresa_a, "Mayorista", "Compra por volumen")

    with empresa(empresa_a.id):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=categoria.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Wholesale",
        )

    with empresa(empresa_a.id), idioma(ingles.pk):
        assert _categorias(contexto_con_sesion) == [("Wholesale", "Compra por volumen")]


def test_la_traduccion_de_otra_empresa_no_se_cuela(
        contexto_con_sesion,
    empresa_a, empresa_b, categoria_de, ingles
):
    de_a = categoria_de(empresa_a, "Mayorista")
    de_b = categoria_de(empresa_b, "Mayorista")

    with empresa(empresa_b.id):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=de_b.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Lo de B",
        )

    with empresa(empresa_a.id), idioma(ingles.pk):
        assert _categorias(contexto_con_sesion) == [("Mayorista", "")]

    assert de_a.pk != de_b.pk


def test_la_categoria_anidada_en_un_rol_tambien_se_traduce(
        contexto_con_sesion,
    empresa_a, crear_entidad, rol_de, categoria_de, ingles
):
    categoria = categoria_de(empresa_a, "Mayorista")

    with empresa(empresa_a.id):
        entidad = crear_entidad("Juan")
        rol_de(entidad, "rol_cliente", categoria_entidad_id=categoria.pk)

        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=categoria.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Wholesale",
        )

    with empresa(empresa_a.id), idioma(ingles.pk):
        resultado = schema.execute_sync(
            "query ($id: ID!) { entidad(id: $id) "
            "{ roles { categoria { nombre } } } }",
            variable_values={"id": str(entidad.pk)},
            context_value=contexto_con_sesion,
        )

    assert resultado.errors is None, resultado.errors
    roles = resultado.data["entidad"]["roles"]
    assert roles[0]["categoria"]["nombre"] == "Wholesale"


def test_traducir_no_agrega_una_consulta_por_categoria(
        contexto_con_sesion,
    empresa_a, categoria_de, ingles
):
    categoria_de(empresa_a, "Mayorista")

    with empresa(empresa_a.id), idioma(ingles.pk):
        with CaptureQueriesContext(connection) as una:
            assert len(_categorias(contexto_con_sesion)) == 1

    for i in range(4):
        categoria_de(empresa_a, f"Categoria {i}")

    with empresa(empresa_a.id), idioma(ingles.pk):
        with CaptureQueriesContext(connection) as cinco:
            assert len(_categorias(contexto_con_sesion)) == 5

    assert len(una) == len(cinco)
