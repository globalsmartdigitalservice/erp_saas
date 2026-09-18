import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from comun.catalogo_modulos import api as modulos
from config.schema import schema
from core.tenancy import empresa
from core.tests.afiliacion import afiliar_en
from core.tests.contexto_graphql import Contexto
from core.tests.permisos import darle_el_permiso
from dominios.seguridad.permisos import content_type_del_ancla

pytestmark = pytest.mark.django_db

Usuario = get_user_model()

PERMISO_DE_LA_GUARDA = "segu_roles_agregar_permiso_al_rol"

CONSULTA = """
{
  catalogoDePermisos { authPermissionId codigo etiqueta pantalla modulo }
}
"""


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def permiso_de_negocio(db):
    def _permiso(codename, nombre=None):
        return Permission.objects.get_or_create(
            content_type=content_type_del_ancla(),
            codename=codename,
            defaults={"name": nombre or codename},
        )[0]

    return _permiso


@pytest.fixture
def ana(empresa_a, activo):
    persona = Usuario.objects.create_user(
        username="ana",
        email="ana@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )
    afiliar_en(empresa_a.id, usuario_id=persona.id, estado_id=activo.id)
    return persona


@pytest.fixture
def edita_roles(ana, empresa_a, activo):
    darle_el_permiso(ana, empresa_a.id, activo.id, PERMISO_DE_LA_GUARDA)
    return ana


def _correr(persona, empresa_id):
    with empresa(empresa_id):
        resultado = schema.execute_sync(CONSULTA, context_value=Contexto(persona))
    assert resultado.errors is None, resultado.errors
    return resultado.data["catalogoDePermisos"]


def _buscar(lineas, codename):
    return next(l for l in lineas if l["codigo"].endswith("." + codename))


def test_sin_el_permiso_de_editar_roles_el_catalogo_no_se_ve(ana, empresa_a):
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(CONSULTA, context_value=Contexto(ana))

    assert resultado.errors is not None


def test_el_catalogo_no_trae_los_permisos_internos_de_django(
    edita_roles, empresa_a, permiso_de_negocio
):
    permiso_de_negocio("segu_roles_crear_rol", "Crear rol")

    codigos = {linea["codigo"] for linea in _correr(edita_roles, empresa_a.id)}

    assert any(codigo.endswith(".segu_roles_crear_rol") for codigo in codigos)
    assert not any("logentry" in codigo or "session" in codigo for codigo in codigos)


def test_sin_catalogo_de_modulos_el_permiso_llega_sin_pantalla(
    edita_roles, empresa_a, permiso_de_negocio
):
    permiso_de_negocio("segu_roles_crear_rol", "Crear rol")

    linea = _buscar(_correr(edita_roles, empresa_a.id), "segu_roles_crear_rol")

    assert linea["etiqueta"] == "Crear rol"
    assert linea["pantalla"] is None
    assert linea["modulo"] is None


def test_con_la_funcionalidad_el_permiso_llega_con_su_pantalla_y_su_modulo(
    edita_roles, empresa_a, permiso_de_negocio, activo
):
    permiso = permiso_de_negocio("segu_roles_crear_rol", "Crear rol")
    seguridad = modulos.crear(
        codigo="SEGU", nombre="Seguridad", estado_id=activo.id
    )
    pantalla = modulos.crear_sub_modulo(
        codigo="SEGU_ROLES",
        modulo_sistema_id=seguridad.id,
        nombre="Roles",
        ruta="/seguridad/roles",
        estado_id=activo.id,
    )
    modulos.crear_funcionalidad(
        sub_modulo_id=pantalla.id,
        auth_permission_id=permiso.id,
        nombre="Crear un rol nuevo",
        estado_id=activo.id,
    )

    linea = _buscar(_correr(edita_roles, empresa_a.id), "segu_roles_crear_rol")

    assert linea["etiqueta"] == "Crear un rol nuevo"
    assert linea["pantalla"] == "Roles"
    assert linea["modulo"] == "Seguridad"
