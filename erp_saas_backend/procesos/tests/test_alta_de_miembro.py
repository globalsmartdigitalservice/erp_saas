import pytest
from django.contrib.auth import get_user_model

from comun.usuarios import api as usuarios
from config.schema import schema
from core.tenancy import empresa
from core.tests.afiliacion import afiliar_en
from core.tests.contexto_graphql import Contexto
from core.tests.permisos import darle_el_permiso
from dominios.seguridad import api as seguridad
from procesos import alta_de_cliente

pytestmark = pytest.mark.django_db

Usuario = get_user_model()

DAR_DE_ALTA = """
mutation ($datos: DarDeAltaMiembroInput!) {
  darDeAltaMiembro(datos: $datos) {
    membresia { id usuario { username } }
    passwordTemporal
  }
}
"""

BUSCAR = """
query ($email: String!) {
  personaPorCorreo(email: $email) { usuarioId nombreCompleto trabajaAca }
}
"""

PERMISO_ALTA = "segu_miembros_dar_de_alta_miembro"
PERMISO_ASIGNAR_ROL = "segu_roles_asignar_rol"
PERMISO_BUSCAR = "segu_miembros_buscar_por_correo"

LUIS = {"username": "luis.condori", "email": "luis@vida.bo", "firstName": "Luis"}


def _alguien_con(farmacia_vida, catalogo_de_altas, username, *codenames):
    empresa_id = farmacia_vida.empresa.pk
    estado_id = catalogo_de_altas["estado_activo"].pk
    persona = Usuario.objects.create_user(
        username=username,
        email=f"{username}@vida.bo",
        password="Kx7pLm9Qw2",
        matriz=farmacia_vida.empresa,
    )
    afiliar_en(empresa_id, usuario_id=persona.pk, estado_id=estado_id)
    darle_el_permiso(persona, empresa_id, estado_id, *codenames)
    return persona


@pytest.fixture
def jefa(farmacia_vida, catalogo_de_altas):
    return _alguien_con(
        farmacia_vida,
        catalogo_de_altas,
        "jefa",
        PERMISO_ALTA,
        PERMISO_ASIGNAR_ROL,
        PERMISO_BUSCAR,
    )


@pytest.fixture
def pedro(farmacia_vida, catalogo_de_altas):
    return _alguien_con(farmacia_vida, catalogo_de_altas, "pedro", PERMISO_ALTA)


@pytest.fixture
def otro_cliente(catalogo_de_altas):
    return alta_de_cliente.dar_de_alta(
        cliente=alta_de_cliente.DatosDelCliente(
            ident_tributaria="7654321",
            razon_social="Ferretería Sur",
            rubro_id=catalogo_de_altas["rubro"].pk,
            pais_id=catalogo_de_altas["bolivia"].pk,
            moneda_oficial_id=catalogo_de_altas["moneda"].pk,
            idioma_default_id=catalogo_de_altas["idioma"].pk,
        ),
        administrador=alta_de_cliente.DatosDelAdministrador(
            username="ramiro.flores", email="ramiro@sur.bo"
        ),
    )


def _como(persona, farmacia_vida, documento, **variables):
    with empresa(farmacia_vida.empresa.pk):
        return schema.execute_sync(
            documento, variable_values=variables, context_value=Contexto(persona)
        )


def test_si_falla_un_paso_no_quedan_ni_la_cuenta_ni_la_membresia(farmacia_vida, jefa):
    resultado = _como(
        jefa, farmacia_vida, DAR_DE_ALTA, datos={"persona": LUIS, "rolIds": ["999999"]}
    )

    assert resultado.errors
    assert usuarios.obtener_por_username("luis.condori") is None


def test_una_cuenta_de_otro_cliente_no_se_da_de_alta(farmacia_vida, jefa, otro_cliente):
    ajena = otro_cliente.administrador.pk

    resultado = _como(jefa, farmacia_vida, DAR_DE_ALTA, datos={"usuarioId": str(ajena)})

    assert [error.message for error in resultado.errors] == [f"No existe el usuario {ajena}."]


def test_con_roles_hace_falta_el_permiso_de_asignarlos(farmacia_vida, pedro):
    resultado = _como(
        pedro,
        farmacia_vida,
        DAR_DE_ALTA,
        datos={"persona": LUIS, "rolIds": [str(farmacia_vida.rol.pk)]},
    )

    assert [error.extensions.get("code") for error in resultado.errors] == ["FORBIDDEN"]
    assert usuarios.obtener_por_username("luis.condori") is None


def test_con_el_permiso_de_roles_queda_dado_de_alta_con_el_rol(farmacia_vida, jefa):
    resultado = _como(
        jefa,
        farmacia_vida,
        DAR_DE_ALTA,
        datos={"persona": LUIS, "rolIds": [str(farmacia_vida.rol.pk)]},
    )

    assert resultado.errors is None, resultado.errors
    alta = resultado.data["darDeAltaMiembro"]
    assert alta["passwordTemporal"]
    with empresa(farmacia_vida.empresa.pk):
        roles = seguridad.historial_de(int(alta["membresia"]["id"]))
    assert [rol.grupo_empresa_id for rol in roles] == [farmacia_vida.rol.pk]


def test_el_buscador_no_encuentra_a_nadie_de_otro_cliente(
    farmacia_vida, jefa, otro_cliente
):
    propia = _como(jefa, farmacia_vida, BUSCAR, email="CARLA@vida.bo")
    ajena = _como(jefa, farmacia_vida, BUSCAR, email="ramiro@sur.bo")

    assert propia.errors is None, propia.errors
    assert propia.data["personaPorCorreo"]["trabajaAca"] is True
    assert ajena.errors is None, ajena.errors
    assert ajena.data["personaPorCorreo"] is None
