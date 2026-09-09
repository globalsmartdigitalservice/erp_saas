import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from config.schema import schema
from core.paginacion import (
    LIMITE_MAXIMO,
    LIMITE_POR_DEFECTO,
    VENTANA_MAXIMA,
    VentanaDemasiadoProfunda,
    limite_seguro,
)
from core.tenancy import empresa
from dominios.entidades import api as entidades

pytestmark = pytest.mark.django_db


@pytest.fixture
def treinta(empresa_a, crear_entidad):
    """Más que la página por defecto, para que haya segunda página."""
    with empresa(empresa_a.id):
        for n in range(30):
            # El nombre va con ceros a la izquierda para que el orden
            # alfabético coincida con el numérico y los tests se puedan
            # leer.
            crear_entidad(f"Entidad {n:02d}", documento=str(n))
    return 30


def test_por_defecto_trae_una_pagina_no_la_tabla(empresa_a, treinta):
    with empresa(empresa_a.id):
        pagina = entidades.listar_entidades()

    assert len(pagina.items) == LIMITE_POR_DEFECTO
    assert pagina.total == 30
    assert pagina.hay_siguiente is True


def test_la_ultima_pagina_no_tiene_siguiente(empresa_a, treinta):
    with empresa(empresa_a.id):
        pagina = entidades.listar_entidades(limite=10, desde=20)

    assert len(pagina.items) == 10
    assert pagina.hay_siguiente is False


def test_el_total_es_de_todas_no_de_la_pagina(empresa_a, treinta):
    with empresa(empresa_a.id):
        pagina = entidades.listar_entidades(limite=5)

    assert len(pagina.items) == 5
    assert pagina.total == 30


def test_el_total_es_solo_de_esta_empresa(empresa_a, empresa_b, crear_entidad):
    with empresa(empresa_b.id):
        for n in range(5):
            crear_entidad(f"De B {n}", documento=f"b{n}")

    with empresa(empresa_a.id):
        crear_entidad("De A", documento="a1")
        pagina = entidades.listar_entidades()

    assert pagina.total == 1
    assert [e.nombre for e in pagina.items] == ["De A"]


def test_ninguna_fila_se_repite_entre_paginas(empresa_a, treinta):
    """Sin `ORDER BY`, la misma fila puede salir en dos páginas y otra en
    ninguna. No revienta nada: faltan clientes en el listado."""
    vistas = []
    with empresa(empresa_a.id):
        for desde in range(0, 30, 10):
            pagina = entidades.listar_entidades(limite=10, desde=desde)
            vistas.extend(e.pk for e in pagina.items)

    assert len(vistas) == 30
    assert len(set(vistas)) == 30, "Hay filas repetidas entre páginas."


def test_dos_entidades_con_el_mismo_nombre_no_bailan(empresa_a, crear_entidad):
    with empresa(empresa_a.id):
        for n in range(6):
            crear_entidad("Juan Pérez", documento=str(n))

        primera = [e.pk for e in entidades.listar_entidades(limite=3).items]
        segunda = [
            e.pk for e in entidades.listar_entidades(limite=3, desde=3).items
        ]

    assert set(primera).isdisjoint(segunda)
    assert len(set(primera) | set(segunda)) == 6


@pytest.mark.parametrize(
    "pedido,esperado",
    [
        (None, LIMITE_POR_DEFECTO),
        (10, 10),
        (0, 1),
        (-5, 1),
        (999_999, LIMITE_MAXIMO),
    ],
)
def test_el_limite_se_acota(pedido, esperado):
    assert limite_seguro(pedido) == esperado


def test_no_se_puede_pedir_mas_de_cien(empresa_a, treinta):
    with empresa(empresa_a.id):
        pagina = entidades.listar_entidades(limite=999_999)

    assert pagina.limite == LIMITE_MAXIMO


def test_la_paginacion_profunda_se_corta(empresa_a):
    with empresa(empresa_a.id):
        with pytest.raises(VentanaDemasiadoProfunda, match="filtros"):
            entidades.listar_entidades(desde=VENTANA_MAXIMA)


def test_el_desplazamiento_negativo_se_rechaza(empresa_a):
    with empresa(empresa_a.id):
        with pytest.raises(VentanaDemasiadoProfunda):
            entidades.listar_entidades(desde=-1)


def test_la_query_devuelve_items_e_info(empresa_a, treinta):
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            "{ entidades(limite: 5, desde: 10) "
            "{ items { nombre } info { total limite desde haySiguiente } } }"
        )

    assert resultado.errors is None
    datos = resultado.data["entidades"]
    assert len(datos["items"]) == 5
    assert datos["info"] == {
        "total": 30,
        "limite": 5,
        "desde": 10,
        "haySiguiente": True,
    }


def test_la_query_avisa_cuando_la_pagina_es_muy_profunda(empresa_a):
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            f"{{ entidades(desde: {VENTANA_MAXIMA}) {{ info {{ total }} }} }}"
        )

    assert resultado.errors is not None
    assert "filtros" in resultado.errors[0].message


def test_paginar_no_agrega_consultas_por_fila(empresa_a, treinta):
    consulta = (
        "{ entidades(limite: %d) { items { nombre tipoEntidad { nombre } "
        "tipoDocumento { nombre } estado { nombre } } } }"
    )

    with empresa(empresa_a.id):
        with CaptureQueriesContext(connection) as con_dos:
            schema.execute_sync(consulta % 2)

        with CaptureQueriesContext(connection) as con_veinte:
            schema.execute_sync(consulta % 20)

    assert len(con_dos) == len(con_veinte)
