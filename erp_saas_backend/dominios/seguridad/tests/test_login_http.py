import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from comun.membresias import api as membresias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ACCESO_BLOQUEADO,
    NOMBRE_ACCESO_EXITO,
    NOMBRE_ACCESO_FALLO,
)

pytestmark = pytest.mark.django_db

Usuario = get_user_model()

URL = "/graphql/"

INGRESAR = """
mutation ($datos: IngresarInput!) {
  ingresar(datos: $datos) {
    necesitaElegirEmpresa
    usuario { username }
    empresas { empresaId razonSocial }
  }
}
"""


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture(autouse=True)
def resultados(catalogo):
    for nombre in (
        NOMBRE_ACCESO_EXITO,
        NOMBRE_ACCESO_BLOQUEADO,
        NOMBRE_ACCESO_FALLO,
    ):
        catalogo["tipologia"](AGRUPADOR.RESULTADO_ACCESO, nombre)


@pytest.fixture
def juan():
    return Usuario.objects.create_user(
        username="juan", email="juan@acme.com", password="Kx7pLm9Qw2"
    )


@pytest.fixture
def en_gimnasio(juan, empresa_a, activo):
    return membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )


@pytest.fixture(autouse=True)
def graphql_encendido(settings):
    """El endpoint solo se monta si el flag está prendido."""
    settings.GRAPHQL_HABILITADO = True
    # Se recarga el urlconf para que el `if` de config/urls.py se
    # vuelva a evaluar con el flag ya puesto.
    from importlib import reload

    import config.urls

    reload(config.urls)
    settings.ROOT_URLCONF = "config.urls"


def _pedir(cliente, consulta, **variables):
    import json

    return cliente.post(
        URL,
        data=json.dumps({"query": consulta, "variables": variables or None}),
        content_type="application/json",
    )


def test_al_entrar_llegan_las_dos_cookies(client, en_gimnasio):
    respuesta = _pedir(
        client,
        INGRESAR,
        datos={"identificador": "juan", "password": "Kx7pLm9Qw2"},
    )

    assert respuesta.json().get("errors") is None
    assert settings.COOKIE_ACCESO in respuesta.cookies
    assert settings.COOKIE_REFRESH in respuesta.cookies


def test_el_token_NO_viaja_en_la_respuesta(client, en_gimnasio):
    respuesta = _pedir(
        client,
        INGRESAR,
        datos={"identificador": "juan", "password": "Kx7pLm9Qw2"},
    )

    cuerpo = respuesta.content.decode()
    valor = respuesta.cookies[settings.COOKIE_ACCESO].value

    assert valor not in cuerpo


def test_la_cookie_es_httponly_y_samesite_lax(client, en_gimnasio):
    respuesta = _pedir(
        client,
        INGRESAR,
        datos={"identificador": "juan", "password": "Kx7pLm9Qw2"},
    )

    cookie = respuesta.cookies[settings.COOKIE_ACCESO]

    assert cookie["httponly"]
    assert cookie["samesite"] == "Lax"


def test_secure_sigue_a_use_https(client, en_gimnasio, settings):
    settings.COOKIE_SECURE = False
    sin_https = _pedir(
        client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"}
    ).cookies[settings.COOKIE_ACCESO]

    settings.COOKIE_SECURE = True
    con_https = _pedir(
        client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"}
    ).cookies[settings.COOKIE_ACCESO]

    assert not sin_https["secure"]
    assert con_https["secure"]


def test_antes_de_entrar_no_hay_nadie(client):
    respuesta = _pedir(client, "{ yo { username } empresaActual }")

    datos = respuesta.json()["data"]
    assert datos["yo"] is None
    assert datos["empresaActual"] is None


def test_despues_de_entrar_la_sesion_sabe_quien_y_donde(
    client, en_gimnasio, empresa_a
):
    _pedir(client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})

    datos = _pedir(client, "{ yo { username } empresaActual }").json()["data"]

    assert datos["yo"]["username"] == "juan"
    assert datos["empresaActual"] == str(empresa_a.id)


def test_al_salir_la_sesion_se_termina(client, en_gimnasio):
    _pedir(client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})

    assert _pedir(client, "mutation { salir }").json()["data"]["salir"] is True

    assert _pedir(client, "{ yo { username } }").json()["data"]["yo"] is None


def test_un_token_manoseado_no_abre_sesion(client, en_gimnasio):
    _pedir(client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})
    client.cookies[settings.COOKIE_ACCESO] = "no.soy.un.token"

    assert _pedir(client, "{ yo { username } }").json()["data"]["yo"] is None


def test_con_dos_empresas_no_se_abre_sesion_hasta_elegir(
    client, juan, en_gimnasio, empresa_b, activo
):
    membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_b.id, estado_id=activo.id
    )

    respuesta = _pedir(
        client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"}
    )

    datos = respuesta.json()["data"]["ingresar"]
    assert datos["necesitaElegirEmpresa"] is True
    assert len(datos["empresas"]) == 2
    assert settings.COOKIE_ACCESO not in respuesta.cookies


def test_elegir_empresa_abre_la_sesion_en_esa(
    client, juan, en_gimnasio, empresa_b, activo
):
    membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_b.id, estado_id=activo.id
    )

    _pedir(
        client,
        """
        mutation ($datos: IngresarInput!, $empresa: ID!) {
          elegirEmpresa(datos: $datos, empresaId: $empresa) {
            usuario { username }
          }
        }
        """,
        datos={"identificador": "juan", "password": "Kx7pLm9Qw2"},
        empresa=str(empresa_b.id),
    )

    datos = _pedir(client, "{ empresaActual }").json()["data"]

    assert datos["empresaActual"] == str(empresa_b.id)


def test_renovar_cambia_las_cookies(client, en_gimnasio):
    _pedir(client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})
    anterior = client.cookies[settings.COOKIE_REFRESH].value

    respuesta = _pedir(client, "mutation { renovarSesion { usuario { username } } }")

    assert respuesta.json().get("errors") is None
    assert respuesta.cookies[settings.COOKIE_REFRESH].value != anterior


def test_renovar_sin_haber_entrado_falla(client, en_gimnasio):
    respuesta = _pedir(client, "mutation { renovarSesion { usuario { username } } }")

    assert respuesta.json()["errors"]


def test_al_fallar_la_renovacion_se_borran_las_cookies(client, en_gimnasio):
    _pedir(client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})
    _pedir(client, "mutation { salir }")
    client.cookies[settings.COOKIE_REFRESH] = "cualquier cosa"

    respuesta = _pedir(client, "mutation { renovarSesion { usuario { username } } }")

    assert respuesta.json()["errors"]
    assert respuesta.cookies[settings.COOKIE_REFRESH].value == ""


def test_las_consultas_devuelven_solo_lo_de_la_empresa_de_la_sesion(
    client, juan, en_gimnasio, empresa_a, empresa_b, activo
):
    ana = Usuario.objects.create_user(
        username="ana", email="ana@otra.com", password="Zq4tRn8Vd3"
    )
    membresias.afiliar(
        usuario_id=ana.id, empresa_id=empresa_b.id, estado_id=activo.id
    )

    _pedir(client, INGRESAR, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})

    datos = _pedir(client, "{ miembros { usuario { username } } }").json()["data"]

    assert [m["usuario"]["username"] for m in datos["miembros"]] == ["juan"]
