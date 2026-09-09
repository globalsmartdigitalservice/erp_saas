import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from comun.membresias import api as membresias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ACCESO_BLOQUEADO,
    NOMBRE_ACCESO_EXITO,
    NOMBRE_ACCESO_FALLO,
)
from dominios.seguridad.permisos import content_type_del_ancla
from dominios.seguridad.permisos_graphql import SIN_PERMISO, SIN_SESION

pytestmark = pytest.mark.django_db

Usuario = get_user_model()
URL = "/graphql/"

# Una mutation protegida cualquiera del módulo 12.
CREAR_ROL = """
mutation ($datos: CrearRolInput!) {
  crearRol(datos: $datos) { id nombre }
}
"""
PERMISO_CREAR_ROL = "segu_roles_crear_rol"


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture(autouse=True)
def resultados_de_acceso(catalogo):
    for nombre in (
        NOMBRE_ACCESO_EXITO,
        NOMBRE_ACCESO_BLOQUEADO,
        NOMBRE_ACCESO_FALLO,
    ):
        catalogo["tipologia"](AGRUPADOR.RESULTADO_ACCESO, nombre)


@pytest.fixture(autouse=True)
def graphql_encendido(settings):
    from importlib import reload

    import config.urls

    settings.GRAPHQL_HABILITADO = True
    reload(config.urls)
    settings.ROOT_URLCONF = "config.urls"


@pytest.fixture
def juan(empresa_a, activo):
    persona = Usuario.objects.create_user(
        username="juan", email="juan@acme.com", password="Kx7pLm9Qw2"
    )
    membresias.afiliar(
        usuario_id=persona.id, empresa_id=empresa_a.id, estado_id=activo.id
    )
    return persona


def _pedir(cliente, consulta, **variables):
    return cliente.post(
        URL,
        data=json.dumps({"query": consulta, "variables": variables or None}),
        content_type="application/json",
    )


def _entrar(cliente, usuario="juan"):
    return _pedir(
        cliente,
        "mutation ($d: IngresarInput!) { ingresar(datos: $d) { usuario { username } } }",
        d={"identificador": usuario, "password": "Kx7pLm9Qw2"},
    )


def _error(respuesta) -> str:
    errores = respuesta.json().get("errors") or []
    return errores[0]["message"] if errores else ""


def _crear_rol(cliente, activo):
    return _pedir(
        cliente, CREAR_ROL, datos={"nombre": "Cajero", "estadoId": str(activo.id)}
    )


def _dar_permiso(persona, codename: str):
    """
    Le da el permiso por el camino del PROVEEDOR (`auth_group`), que es el
    que resuelve el backend para `is_staff`.
    """
    from django.contrib.auth.models import Group

    permiso, _ = Permission.objects.get_or_create(
        content_type=content_type_del_ancla(), codename=codename, defaults={"name": codename}
    )
    grupo, _ = Group.objects.get_or_create(name="prueba")
    grupo.permissions.add(permiso)
    persona.groups.add(grupo)
    return permiso


def test_sin_sesion_una_mutation_protegida_se_rechaza(client, activo):
    assert _error(_crear_rol(client, activo)) == SIN_SESION


def test_el_login_NO_esta_protegido(client, juan):
    assert _entrar(client).json().get("errors") is None


def test_con_sesion_pero_sin_el_permiso_se_rechaza(client, juan, activo):
    _entrar(client)

    assert _error(_crear_rol(client, activo)) == SIN_PERMISO


def test_el_mensaje_no_dice_QUE_permiso_falta(client, juan, activo):
    _entrar(client)

    assert PERMISO_CREAR_ROL not in _error(_crear_rol(client, activo))


def test_con_el_permiso_pasa(client, juan, activo):
    juan.is_staff = True  # para resolver por auth_group
    juan.save(update_fields=["is_staff"])
    _dar_permiso(juan, PERMISO_CREAR_ROL)
    _entrar(client)

    respuesta = _crear_rol(client, activo)

    assert respuesta.json().get("errors") is None
    assert respuesta.json()["data"]["crearRol"]["nombre"] == "Cajero"


def test_el_superusuario_pasa_sin_permisos(client, empresa_a, activo):
    jefe = Usuario.objects.create_superuser(
        username="jefe", email="jefe@proveedor.com", password="Kx7pLm9Qw2"
    )
    membresias.afiliar(
        usuario_id=jefe.id, empresa_id=empresa_a.id, estado_id=activo.id
    )
    _entrar(client, "jefe")

    assert _crear_rol(client, activo).json().get("errors") is None


def test_una_mutation_sin_decorador_funciona_con_solo_estar_logueado(
    client, juan, catalogo
):
    """No es un agujero, es la decisión: los decoradores se ponen al final y
    mientras tanto la mutation funciona."""
    _entrar(client)

    respuesta = _pedir(
        client,
        """
        mutation ($d: CrearTipologiaInput!) {
          crearTipologia(datos: $d) { id nombre }
        }
        """,
        d={
            "agrupador": AGRUPADOR.RUBRO.value,
            "nombre": "TURISMO",
            "estado": "ACTIVO",
        },
    )

    # Puede fallar por reglas de negocio, pero NUNCA por permisos.
    assert _error(respuesta) not in (SIN_PERMISO, SIN_SESION)
