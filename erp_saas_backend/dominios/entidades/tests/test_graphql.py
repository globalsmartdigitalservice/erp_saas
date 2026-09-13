import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from config.schema import schema
from core.tenancy import empresa
from dominios.entidades import api as entidades

pytestmark = pytest.mark.django_db


def test_query_entidades(contexto_con_sesion, empresa_a, crear_entidad):
    with empresa(empresa_a.id):
        crear_entidad("Juan", documento="1234567")

        resultado = schema.execute_sync(
            "{ entidades { items { nombre documento tipoEntidad { nombre } "
            "estado { nombre } } info { total } } }",
            context_value=contexto_con_sesion,
        )

    assert resultado.errors is None
    assert resultado.data["entidades"]["items"] == [
        {
            "nombre": "Juan",
            "documento": "1234567",
            "tipoEntidad": {"nombre": "PERSONA NATURAL"},
            "estado": {"nombre": "ACTIVO"},
        }
    ]
    assert resultado.data["entidades"]["info"]["total"] == 1


def test_la_lista_no_trae_las_colecciones(
    contexto_con_sesion, empresa_a, crear_entidad, rol_de
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        rol_de(juan)

        resultado = schema.execute_sync(
            "{ entidades { items { nombre roles { id } } } }",
            context_value=contexto_con_sesion,
        )

    assert resultado.errors is None
    assert resultado.data["entidades"]["items"] == [{"nombre": "Juan", "roles": []}]


def test_el_detalle_si_trae_las_colecciones(
        contexto_con_sesion,
    empresa_a, crear_entidad, rol_de, crear_contacto, catalogo_entidades
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        rol_de(juan)
        entidades.crear_direccion(
            entidad_id=juan.pk,
            tipo_id=catalogo_entidades["dir_domicilio"].pk,
            estado_id=catalogo_entidades["estado_activo"].pk,
            calle="Sucre",
        )
        crear_contacto(juan)

        resultado = schema.execute_sync(
            'query ($id: ID!) { entidad(id: $id) { nombre '
            "roles { tipoRol { nombre } } direcciones { calle } "
            "contactos { nombre } } }",
            variable_values={"id": str(juan.pk)},
            context_value=contexto_con_sesion,
        )

    assert resultado.errors is None
    assert resultado.data["entidad"] == {
        "nombre": "Juan",
        "roles": [{"tipoRol": {"nombre": "CLIENTE"}}],
        "direcciones": [{"calle": "Sucre"}],
        "contactos": [{"nombre": "Ana"}],
    }


def test_la_entidad_de_otra_empresa_devuelve_null(
        contexto_con_sesion,
    empresa_a, empresa_b, crear_entidad
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

    with empresa(empresa_b.id):
        resultado = schema.execute_sync(
            'query ($id: ID!) { entidad(id: $id) { nombre } }',
            variable_values={"id": str(juan.pk)},
            context_value=contexto_con_sesion,
        )

    assert resultado.errors is None
    assert resultado.data["entidad"] is None


def test_listar_entidades_no_crece_con_la_cantidad(
    contexto_con_sesion, empresa_a, crear_entidad
):
    with empresa(empresa_a.id):
        crear_entidad("Sola", documento="1")

        with CaptureQueriesContext(connection) as con_una:
            schema.execute_sync(
                "{ entidades { items { nombre tipoEntidad { nombre } "
                "tipoDocumento { nombre } estado { nombre } } } }",
                context_value=contexto_con_sesion,
            )

        for n in range(2, 11):
            crear_entidad(f"Entidad {n}", documento=str(n))

        with CaptureQueriesContext(connection) as con_diez:
            resultado = schema.execute_sync(
                "{ entidades { items { nombre tipoEntidad { nombre } "
                "tipoDocumento { nombre } estado { nombre } } } }",
                context_value=contexto_con_sesion,
            )

    assert resultado.errors is None
    # Diez entran en la página por defecto (25), así que la comparación
    # sigue siendo entre 1 y 10 filas de verdad.
    assert len(resultado.data["entidades"]["items"]) == 10
    assert len(con_diez) == len(con_una), (
        f"Con 1 entidad: {len(con_una)} consultas. Con 10: {len(con_diez)}. "
        f"Si el número creció, alguien resolvió una tipología de a una en "
        f"vez de traerlas por lote."
    )


def test_mutation_crear_entidad(empresa_a, catalogo_entidades):
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            """
            mutation ($datos: CrearEntidadInput!) {
              crearEntidad(datos: $datos) { nombre documento }
            }
            """,
            variable_values={
                "datos": {
                    "tipoEntidadId": str(catalogo_entidades["tipo_natural"].pk),
                    "nombre": "Juan",
                    "tipoDocumentoId": str(catalogo_entidades["doc_ci"].pk),
                    "estadoId": str(catalogo_entidades["estado_activo"].pk),
                    "documento": "  1234567  ",
                }
            },
        )

    assert resultado.errors is None
    # El service normaliza el documento antes de guardarlo.
    assert resultado.data["crearEntidad"] == {
        "nombre": "Juan",
        "documento": "1234567",
    }


def test_el_input_no_acepta_empresa_id(empresa_a, catalogo_entidades):
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            """
            mutation ($datos: CrearEntidadInput!) {
              crearEntidad(datos: $datos) { nombre }
            }
            """,
            variable_values={
                "datos": {
                    "tipoEntidadId": str(catalogo_entidades["tipo_natural"].pk),
                    "nombre": "Juan",
                    "tipoDocumentoId": str(catalogo_entidades["doc_ci"].pk),
                    "estadoId": str(catalogo_entidades["estado_activo"].pk),
                    "empresaId": "999",
                }
            },
        )

    assert resultado.errors is not None
    assert "empresaId" in str(resultado.errors[0])


def test_el_error_del_service_llega_tal_cual(empresa_a, crear_entidad):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan", documento="1234567")

        resultado = schema.execute_sync(
            """
            mutation ($id: ID!, $datos: ActualizarEntidadInput!) {
              actualizarEntidad(id: $id, datos: $datos) { nombre }
            }
            """,
            variable_values={
                "id": str(juan.pk),
                "datos": {"tipoEntidadId": "999999"},
            },
        )

    assert resultado.errors is not None
    assert "Se esperaba un tipo de entidad" in str(resultado.errors[0])


def test_el_error_no_delata_la_categoria_de_otra_empresa(
    empresa_a, empresa_b, crear_entidad, crear_categoria, catalogo_entidades
):
    with empresa(empresa_b.id):
        categoria_de_b = crear_categoria()

    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

        resultado = schema.execute_sync(
            """
            mutation ($datos: CrearRolEntidadInput!) {
              crearRolEntidad(datos: $datos) { id }
            }
            """,
            variable_values={
                "datos": {
                    "entidadId": str(juan.pk),
                    "tipoRolId": str(catalogo_entidades["rol_cliente"].pk),
                    "estadoId": str(catalogo_entidades["estado_activo"].pk),
                    "categoriaEntidadId": str(categoria_de_b.pk),
                }
            },
        )

    assert resultado.errors is not None
    mensaje = str(resultado.errors[0]).lower()
    assert "no existe" in mensaje
    assert "permiso" not in mensaje
    assert "otra empresa" not in mensaje


def test_mutation_desactivar_contacto_devuelve_el_estado_de_baja(
    empresa_a, crear_entidad, crear_contacto, catalogo_entidades
):
    catalogo_entidades["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)

    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        contacto = crear_contacto(juan)

        resultado = schema.execute_sync(
            "mutation ($id: ID!) { desactivarContactoEntidad(id: $id) "
            "{ id estado { nombre } } }",
            variable_values={"id": str(contacto.pk)},
        )

    assert resultado.errors is None
    devuelto = resultado.data["desactivarContactoEntidad"]
    assert devuelto["estado"]["nombre"] == NOMBRE_ESTADO_BAJA
