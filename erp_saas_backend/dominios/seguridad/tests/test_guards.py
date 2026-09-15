import json

import pytest
from django.contrib.auth import get_user_model

from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ACCESO_BLOQUEADO,
    NOMBRE_ACCESO_EXITO,
    NOMBRE_ACCESO_FALLO,
)
from config.schema import schema
from core.tenancy import empresa
from core.tests.afiliacion import afiliar_en
from core.tests.permisos import darle_el_permiso
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
PERMISO_LISTAR_MIEMBROS = "segu_miembros_listar"
PERMISO_VER_USUARIO = "segu_usuarios_ver"


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
    afiliar_en(empresa_a.id, usuario_id=persona.id, estado_id=activo.id)
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


def _error(response) -> str:
    errores = response.json().get("errors") or []
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
            "_Request", (), {"user": usuario, "META": {}, "COOKIES": {}}
        )()
        self.response = None


def _crear_rol(cliente, activo):
    return _pedir(
        cliente, CREAR_ROL, datos={"nombre": "Cajero", "estadoId": str(activo.id)}
    )



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
    darle_el_permiso(juan, empresa_a.id, activo.id, PERMISO_CREAR_ROL)
    _entrar(client)

    response = _crear_rol(client, activo)

    assert response.json().get("errors") is None
    assert response.json()["data"]["crearRol"]["nombre"] == "Cajero"


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


def test_la_lista_de_miembros_exige_permiso(client, juan, empresa_a, activo):
    """Antes bastaba con estar logueado, y un cajero veía de cada compañero el
    correo, si estaba de baja y `debeCambiarPassword` — o sea la lista de quién
    sigue con la contraseña temporal que le dictaron."""
    _entrar(client)
    assert _error(_pedir(client, "{ miembros { id } }")) == SIN_PERMISO

    darle_el_permiso(juan, empresa_a.id, activo.id, PERMISO_LISTAR_MIEMBROS)
    _entrar(client)

    assert _pedir(client, "{ miembros { id } }").json().get("errors") is None


def test_la_ficha_de_otra_sucursal_responde_como_si_no_existiera(
    client, juan, empresa_a, sucursal_a, activo
):
    """Leer no puede ser más ancho que escribir: si Juan no puede editar a
    alguien de otra sucursal, tampoco ve su ficha.

    Y la respuesta tiene que ser LA MISMA que para un id inventado. Si dijera
    "trabaja en otra sucursal" confirmaría que el id existe, y probando números
    se arma el padrón del cliente entero."""
    sofia = Usuario.objects.create_user(
        username="sofia",
        email="sofia@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )
    afiliar_en(sucursal_a.id, usuario_id=sofia.id, estado_id=activo.id)
    darle_el_permiso(juan, empresa_a.id, activo.id, PERMISO_VER_USUARIO)
    _entrar(client)

    consulta = "query ($id: ID!) { usuario(id: $id) { username } }"
    otra_sucursal = _error(_pedir(client, consulta, id=str(sofia.id)))
    inventado = _error(_pedir(client, consulta, id="999999"))

    assert otra_sucursal == f"No existe el usuario {sofia.id}."
    assert inventado == "No existe el usuario 999999."

def test_una_mutation_sin_decorador_funciona_con_solo_estar_logueado(
    client, juan, catalogo
):
    """No es un agujero, es la decisión: los decoradores se ponen al final y
    mientras tanto la mutation funciona."""
    _entrar(client)

    response = _pedir(
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
    assert _error(response) not in (SIN_PERMISO, SIN_SESION)
