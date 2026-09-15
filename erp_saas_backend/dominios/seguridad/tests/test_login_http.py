import datetime

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from comun.membresias import api as membresias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ACCESO_BLOQUEADO,
    NOMBRE_ACCESO_EXITO,
    NOMBRE_ACCESO_FALLO,
    NOMBRE_ESTADO_BAJA,
)
from core.tenancy import empresa
from core.tests.afiliacion import afiliar_en
from core.tests.permisos import darle_el_permiso
from dominios.seguridad.models import SesionAcceso

pytestmark = pytest.mark.django_db

Usuario = get_user_model()

URL = "/graphql/"

LOGIN = """
mutation ($datos: LoginInput!) {
  login(datos: $datos) {
    necesitaElegirEmpresa
    usuario { username }
    empresas { empresaId razonSocial }
  }
}
"""


# Una consulta cualquiera que necesite la empresa de la sesión: sin ella,
# el aislamiento levanta y la respuesta viene con errores. Se usa `roles`
# y no `miembros` porque esta sonda mide la SESIÓN, y `miembros` pasó a
# pedir permiso: mezclaría las dos cosas.
SONDA = "{ roles { id } }"


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
def juan(empresa_a):
    return Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )


@pytest.fixture
def en_gimnasio(juan, empresa_a, activo):
    return afiliar_en(empresa_a.id, usuario_id=juan.id, estado_id=activo.id)


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


def _pedir(cliente, consulta, *, cabeceras=None, **variables):
    import json

    return cliente.post(
        URL,
        data=json.dumps({"query": consulta, "variables": variables or None}),
        content_type="application/json",
        headers=cabeceras or {},
    )


def test_al_entrar_llegan_las_dos_cookies(client, en_gimnasio):
    respuesta = _pedir(
        client,
        LOGIN,
        datos={"identificador": "juan", "password": "Kx7pLm9Qw2"},
    )

    assert respuesta.json().get("errors") is None
    assert settings.COOKIE_ACCESO in respuesta.cookies
    assert settings.COOKIE_REFRESH in respuesta.cookies


def test_el_token_NO_viaja_en_la_respuesta(client, en_gimnasio):
    respuesta = _pedir(
        client,
        LOGIN,
        datos={"identificador": "juan", "password": "Kx7pLm9Qw2"},
    )

    cuerpo = respuesta.content.decode()
    valor = respuesta.cookies[settings.COOKIE_ACCESO].value

    assert valor not in cuerpo


def test_la_cookie_es_httponly_y_samesite_lax(client, en_gimnasio):
    respuesta = _pedir(
        client,
        LOGIN,
        datos={"identificador": "juan", "password": "Kx7pLm9Qw2"},
    )

    cookie = respuesta.cookies[settings.COOKIE_ACCESO]

    assert cookie["httponly"]
    assert cookie["samesite"] == "Lax"


def test_secure_sigue_a_use_https(client, en_gimnasio, settings):
    settings.COOKIE_SECURE = False
    sin_https = _pedir(
        client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"}
    ).cookies[settings.COOKIE_ACCESO]

    settings.COOKIE_SECURE = True
    con_https = _pedir(
        client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"}
    ).cookies[settings.COOKIE_ACCESO]

    assert not sin_https["secure"]
    assert con_https["secure"]


def test_antes_de_entrar_no_hay_nadie(client):
    respuesta = _pedir(client, "{ me { username } empresaActual }")

    datos = respuesta.json()["data"]
    assert datos["me"] is None
    assert datos["empresaActual"] is None


def test_despues_de_entrar_la_sesion_sabe_quien_y_donde(
    client, en_gimnasio, empresa_a
):
    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})

    datos = _pedir(client, "{ me { username } empresaActual }").json()["data"]

    assert datos["me"]["username"] == "juan"
    assert datos["empresaActual"] == str(empresa_a.id)


def test_al_salir_la_sesion_se_termina(client, en_gimnasio):
    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})

    assert _pedir(client, "mutation { logout }").json()["data"]["logout"] is True

    assert _pedir(client, "{ me { username } }").json()["data"]["me"] is None


def test_un_token_manoseado_no_abre_sesion(client, en_gimnasio):
    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})
    client.cookies[settings.COOKIE_ACCESO] = "no.soy.un.token"

    assert _pedir(client, "{ me { username } }").json()["data"]["me"] is None


def test_con_dos_empresas_no_se_abre_sesion_hasta_elegir(
    client, juan, en_gimnasio, sucursal_a, activo
):
    afiliar_en(sucursal_a.id, usuario_id=juan.id, estado_id=activo.id)

    respuesta = _pedir(
        client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"}
    )

    datos = respuesta.json()["data"]["login"]
    assert datos["necesitaElegirEmpresa"] is True
    assert len(datos["empresas"]) == 2
    # Con dos cuentas del mismo correo, cualquiera de las dos fichas sería
    # arbitraria: no se manda ninguna hasta que elija.
    assert datos["usuario"] is None
    assert settings.COOKIE_ACCESO not in respuesta.cookies


def test_elegir_empresa_abre_la_sesion_en_esa(
    client, juan, en_gimnasio, sucursal_a, activo
):
    afiliar_en(sucursal_a.id, usuario_id=juan.id, estado_id=activo.id)

    _pedir(
        client,
        """
        mutation ($datos: LoginInput!, $empresa: ID!) {
          elegirEmpresa(datos: $datos, empresaId: $empresa) {
            usuario { username }
          }
        }
        """,
        datos={"identificador": "juan", "password": "Kx7pLm9Qw2"},
        empresa=str(sucursal_a.id),
    )

    datos = _pedir(client, "{ empresaActual }").json()["data"]

    assert datos["empresaActual"] == str(sucursal_a.id)


def test_renovar_cambia_las_cookies(client, en_gimnasio):
    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})
    anterior = client.cookies[settings.COOKIE_REFRESH].value

    respuesta = _pedir(client, "mutation { refreshSession { usuario { username } } }")

    assert respuesta.json().get("errors") is None
    assert respuesta.cookies[settings.COOKIE_REFRESH].value != anterior


def test_renovar_sin_haber_entrado_falla(client, en_gimnasio):
    respuesta = _pedir(client, "mutation { refreshSession { usuario { username } } }")

    assert respuesta.json()["errors"]


def test_al_fallar_la_renovacion_se_borran_las_cookies(client, en_gimnasio):
    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})
    _pedir(client, "mutation { logout }")
    client.cookies[settings.COOKIE_REFRESH] = "cualquier cosa"

    respuesta = _pedir(client, "mutation { refreshSession { usuario { username } } }")

    assert respuesta.json()["errors"]
    assert respuesta.cookies[settings.COOKIE_REFRESH].value == ""


def test_las_consultas_devuelven_solo_lo_de_la_empresa_de_la_sesion(
    client, juan, en_gimnasio, empresa_a, empresa_b, activo
):
    darle_el_permiso(juan, empresa_a.id, activo.id, "segu_miembros_listar")
    ana = Usuario.objects.create_user(
        username="ana",
        email="ana@otra.com",
        password="Zq4tRn8Vd3",
        matriz=empresa_b,
    )
    afiliar_en(empresa_b.id, usuario_id=ana.id, estado_id=activo.id)

    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})

    datos = _pedir(client, "{ miembros { usuario { username } } }").json()["data"]

    assert [m["usuario"]["username"] for m in datos["miembros"]] == ["juan"]


def test_la_cabecera_de_empresa_no_le_gana_al_token(
    client, en_gimnasio, empresa_a, empresa_b
):
    """La empresa del token va firmada; la de la cabecera no.

    Sale del ORDEN de los middlewares, que no se ve desde acá, y darlo vuelta
    no rompe nada: contesta con los datos de la otra empresa. El frontend
    manda esa cabecera desde el localStorage, así que una guardada de antes le
    cambiaría la empresa a una sesión recién abierta.

    Juan NO es miembro de `empresa_b`: la cabecera no tiene que servir ni
    siquiera para ir a donde la persona sí podría entrar."""
    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})

    respuesta = _pedir(
        client,
        "{ empresaActual }",
        cabeceras={"x-empresa-id": str(empresa_b.id)},
    )

    assert respuesta.json()["data"]["empresaActual"] == str(empresa_a.id)


def test_al_desafiliar_la_sesion_abierta_muere_EN_EL_ACTO(
    client, en_gimnasio, empresa_a, catalogo
):
    """El agujero grande que se tapó.

    Antes, dar de baja a alguien no lo sacaba: su token ya llevaba la
    empresa adentro y la renovación tampoco miraba la membresía, así que
    se quedaba adentro mientras siguiera renovando. **No era una ventana
    de 15 minutos: era indefinida.**
    """
    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})
    assert _pedir(client, SONDA).json().get("errors") is None

    baja = catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)
    with empresa(empresa_a.id):
        membresias.desafiliar(membresia_id=en_gimnasio.id, estado_baja_id=baja.id)

    # Sin volver a entrar ni esperar nada: la siguiente petición ya no pasa.
    assert _pedir(client, SONDA).json().get("errors") is not None


def test_la_sesion_olvidada_se_vence_sola(client, en_gimnasio, empresa_a):
    """La terminal que alguien dejó abierta y se fue.

    Nadie la cierra —la gente cierra el navegador, no la sesión—, así que
    el `fin` queda vacío para siempre. Lo que la corta es la inactividad.
    """
    _pedir(client, LOGIN, datos={"identificador": "juan", "password": "Kx7pLm9Qw2"})
    assert _pedir(client, SONDA).json().get("errors") is None

    with empresa(empresa_a.id):
        sesion = SesionAcceso.objects.first()
        sesion.ultima_actividad = (
            datetime.datetime.now(datetime.UTC)
            - settings.SESSION_IDLE_TIMEOUT
            - datetime.timedelta(minutes=1)
        )
        sesion.save(update_fields=["ultima_actividad"])

    assert sesion.fin is None  # nadie la cerró
    assert _pedir(client, SONDA).json().get("errors") is not None
