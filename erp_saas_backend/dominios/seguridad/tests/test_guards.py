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
from config.schema import schema
from core.tenancy import empresa
from dominios.seguridad import api as seguridad
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
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
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
        "mutation ($d: LoginInput!) { login(datos: $d) { usuario { username } } }",
        d={"identificador": usuario, "password": "Kx7pLm9Qw2"},
    )


def _error(respuesta) -> str:
    errores = respuesta.json().get("errors") or []
    return errores[0]["message"] if errores else ""


def _mensajes(resultado) -> list[str]:
    """Los mensajes de un `execute_sync`, que devuelve el resultado en vez de
    una respuesta HTTP."""
    return [e.message for e in (resultado.errors or [])]


class _ContextoDeDjango:
    """Una petición como la que deja el `/admin/`: con `user` puesto por Django
    y SIN la marca del middleware del ERP. El ayudante normal de tests pone las
    dos, así que no sirve para probar esta diferencia."""

    def __init__(self, usuario):
        self.request = type(
            "_Peticion", (), {"user": usuario, "META": {}, "COOKIES": {}}
        )()
        self.response = None


def _crear_rol(cliente, activo):
    return _pedir(
        cliente, CREAR_ROL, datos={"nombre": "Cajero", "estadoId": str(activo.id)}
    )


def _darle_el_permiso(persona, empresa_a, activo, codename: str):
    """Por el camino real de un cliente: un rol de su empresa, con el
    permiso adentro, asignado a su membresía."""
    permiso, _ = Permission.objects.get_or_create(
        content_type=content_type_del_ancla(),
        codename=codename,
        defaults={"name": codename},
    )
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Supervisor", estado_id=activo.id)
        seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=permiso.id)
        seguridad.asignar_rol(
            membresia_id=membresias.membresia_de(persona.id).id,
            grupo_id=rol.id,
            estado_id=activo.id,
        )
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


def test_con_el_permiso_pasa(client, juan, empresa_a, activo):
    _darle_el_permiso(juan, empresa_a, activo, PERMISO_CREAR_ROL)
    _entrar(client)

    respuesta = _crear_rol(client, activo)

    assert respuesta.json().get("errors") is None
    assert respuesta.json()["data"]["crearRol"]["nombre"] == "Cajero"


def test_el_superusuario_pasa_sin_permisos(db, activo, empresa_a):
    """La llave maestra del proveedor: `permisos_graphql.py` deja pasar al
    superusuario sin mirar ningún permiso.

    ⚠️ Este test se había BORRADO el 2026-09-11 con el argumento de que esa
    línea era inalcanzable —un superusuario no tiene cliente, así que no tiene
    membresía, así que no abre sesión en el ERP—. Era falso: la cookie del
    `/admin/` autentica en GraphQL igual. Hoy esa puerta la gobierna
    `TRUST_DJANGO_SESSION`, pero la línea sigue viva y se prueba."""
    from core.tests.contexto_graphql import Contexto

    jefe = Usuario.objects.create_superuser(
        username="proveedor.jefe", email="jefe@erp.test", password="Kx7pLm9Qw2"
    )

    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            CREAR_ROL,
            variable_values={"datos": {"nombre": "Cajero", "estadoId": str(activo.id)}},
            context_value=Contexto(jefe),
        )

    assert resultado.errors is None
    assert resultado.data["crearRol"]["nombre"] == "Cajero"


def test_la_cookie_del_admin_no_entra_cuando_el_interruptor_esta_cerrado(
    db, activo, empresa_a, settings
):
    """Lo que promete `TRUST_DJANGO_SESSION`, y que nada más verifica.

    Se arma una petición como la que deja el `/admin/`: con `user` puesto por
    Django y SIN la marca del middleware del ERP. Cerrado, no entra; abierto,
    entra — y esa es toda la diferencia entre producción y desarrollo."""
    jefe = Usuario.objects.create_superuser(
        username="proveedor.jefe2", email="jefe2@erp.test", password="Kx7pLm9Qw2"
    )
    contexto = _ContextoDeDjango(jefe)

    settings.TRUST_DJANGO_SESSION = False
    cerrado = schema.execute_sync(
        CREAR_ROL,
        variable_values={"datos": {"nombre": "Cajero", "estadoId": str(activo.id)}},
        context_value=contexto,
    )
    assert SIN_SESION in _mensajes(cerrado)

    settings.TRUST_DJANGO_SESSION = True
    with empresa(empresa_a.id):
        abierto = schema.execute_sync(
            CREAR_ROL,
            variable_values={
                "datos": {"nombre": "Cajero", "estadoId": str(activo.id)}
            },
            context_value=contexto,
        )
    assert abierto.errors is None
    assert abierto.data["crearRol"]["nombre"] == "Cajero"


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
