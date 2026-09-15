import datetime

import pytest
from django.contrib.auth import get_user_model

from comun.empresas.services.empresa import NOMBRE_TIPO_SUCURSAL
from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from config.schema import schema
from core.tenancy import empresa
from core.tests.afiliacion import afiliar_en
from core.tests.contexto_graphql import Contexto
from core.tests.permisos import darle_el_permiso
from dominios.seguridad import api as seguridad
from procesos import alta_de_sucursal

pytestmark = pytest.mark.django_db

Usuario = get_user_model()

LLAVE = "segu_roles_asignar_rol"
PERMISO_ACTUALIZAR = "segu_usuarios_actualizar_usuario"
PERMISO_DESACTIVAR = "segu_usuarios_desactivar_usuario"
PERMISO_DESAFILIAR = "segu_miembros_desafiliar"
PERMISO_QUITAR_ROL = "segu_roles_quitar_rol"
PERMISO_LISTAR = "segu_miembros_listar"

ULTIMA_PERSONA = "última persona que puede administrar"

ACTUALIZAR = """
mutation ($id: ID!, $datos: ActualizarUsuarioInput!) {
  actualizarUsuario(id: $id, datos: $datos) { email }
}
"""

DESACTIVAR = """
mutation ($id: ID!) {
  desactivarUsuario(id: $id) { isActive }
}
"""

DESAFILIAR = """
mutation ($datos: DesafiliarInput!) {
  desafiliar(datos: $datos) { id }
}
"""

QUITAR_ROL = """
mutation ($asignacionId: ID!) {
  quitarRol(asignacionId: $asignacionId) { id }
}
"""


@pytest.fixture(autouse=True)
def baja(catalogo_de_altas):
    return catalogo_de_altas["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)


@pytest.fixture
def activo(catalogo_de_altas):
    return catalogo_de_altas["estado_activo"]


@pytest.fixture
def central(farmacia_vida):
    return farmacia_vida.empresa


def _persona(central, username):
    return Usuario.objects.create_user(
        username=username,
        email=f"{username}@vida.bo",
        password="Kx7pLm9Qw2",
        matriz=central,
    )


@pytest.fixture
def diego(central):
    return _persona(central, "diego")


@pytest.fixture
def norte(central, diego):
    tipo = tipologias.obtener_del_sistema(AGRUPADOR.TIPO_EMPRESA, NOMBRE_TIPO_SUCURSAL)
    return alta_de_sucursal.dar_de_alta(
        alta_de_sucursal.DatosDeLaSucursal(
            padre_id=central.pk,
            razon_social="Farmacia Vida - Norte",
            tipo_empresa_id=tipo.pk,
            encargado_username=diego.username,
        )
    ).empresa


def _como(persona, empresa_id, documento, **variables):
    with empresa(empresa_id):
        return schema.execute_sync(
            documento, variable_values=variables, context_value=Contexto(persona)
        )


def _mensajes(resultado) -> str:
    return " ".join(error.message for error in resultado.errors or [])


def _codigos(resultado) -> list[str]:
    return [error.extensions.get("code") for error in resultado.errors or []]


def _membresia(persona, en):
    with empresa(en.pk):
        return membresias.membresia_de(persona.pk)


def _asignacion(persona, en, nombre_rol):
    with empresa(en.pk):
        historial = seguridad.historial_de(membresias.membresia_de(persona.pk).pk)
    return next(a for a in historial if a.grupo_empresa.nombre == nombre_rol)


def test_el_encargado_de_una_sucursal_no_edita_a_quien_trabaja_solo_en_la_matriz(
    central, norte, diego, activo
):
    ana = _persona(central, "ana")
    afiliar_en(central.pk, usuario_id=ana.pk, estado_id=activo.pk)
    darle_el_permiso(diego, norte.pk, activo.pk, PERMISO_ACTUALIZAR)

    resultado = _como(
        diego, norte.pk, ACTUALIZAR, id=str(ana.pk), datos={"email": "otra@vida.bo"}
    )

    ana.refresh_from_db()
    assert _mensajes(resultado) == f"No existe el usuario {ana.pk}."
    assert ana.email == "ana@vida.bo"


def test_sin_permiso_en_todas_sus_empresas_no_se_desactiva_la_cuenta(
    central, norte, diego, activo
):
    juan = _persona(central, "juan")
    afiliar_en(central.pk, usuario_id=juan.pk, estado_id=activo.pk)
    afiliar_en(norte.pk, usuario_id=juan.pk, estado_id=activo.pk)
    darle_el_permiso(diego, norte.pk, activo.pk, PERMISO_DESACTIVAR)

    resultado = _como(diego, norte.pk, DESACTIVAR, id=str(juan.pk))

    juan.refresh_from_db()
    assert _codigos(resultado) == ["FORBIDDEN"]
    assert juan.is_active is True


def test_con_permiso_en_todas_sus_empresas_se_desactiva_la_cuenta(
    central, norte, diego, activo
):
    juan = _persona(central, "juan")
    afiliar_en(central.pk, usuario_id=juan.pk, estado_id=activo.pk)
    afiliar_en(norte.pk, usuario_id=juan.pk, estado_id=activo.pk)
    afiliar_en(central.pk, usuario_id=diego.pk, estado_id=activo.pk)
    darle_el_permiso(
        diego, central.pk, activo.pk, PERMISO_DESACTIVAR, nombre_rol="Supervisor central"
    )
    darle_el_permiso(
        diego, norte.pk, activo.pk, PERMISO_DESACTIVAR, nombre_rol="Supervisor norte"
    )

    resultado = _como(diego, norte.pk, DESACTIVAR, id=str(juan.pk))

    assert resultado.errors is None, resultado.errors
    juan.refresh_from_db()
    assert juan.is_active is False


def test_no_se_da_de_baja_a_la_ultima_persona_que_administra_la_empresa(
    norte, diego, activo, baja
):
    darle_el_permiso(diego, norte.pk, activo.pk, LLAVE, PERMISO_DESAFILIAR)
    membresia = _membresia(diego, norte)

    resultado = _como(
        diego,
        norte.pk,
        DESAFILIAR,
        datos={"membresiaId": str(membresia.pk), "estadoBajaId": str(baja.pk)},
    )

    assert ULTIMA_PERSONA in _mensajes(resultado)
    assert _membresia(diego, norte).estado_id == activo.pk


def test_no_se_le_quita_el_rol_a_la_ultima_persona_que_administra_la_empresa(
    norte, diego, activo
):
    darle_el_permiso(diego, norte.pk, activo.pk, LLAVE, PERMISO_QUITAR_ROL)
    llave = _asignacion(diego, norte, "Supervisor")

    resultado = _como(diego, norte.pk, QUITAR_ROL, asignacionId=str(llave.pk))

    assert ULTIMA_PERSONA in _mensajes(resultado)
    assert _asignacion(diego, norte, "Supervisor").estado_id == activo.pk


def test_no_se_desactiva_la_cuenta_de_la_ultima_persona_que_administra_la_empresa(
    norte, diego, activo
):
    darle_el_permiso(diego, norte.pk, activo.pk, LLAVE, PERMISO_DESACTIVAR)

    resultado = _como(diego, norte.pk, DESACTIVAR, id=str(diego.pk))

    diego.refresh_from_db()
    assert ULTIMA_PERSONA in _mensajes(resultado)
    assert diego.is_active is True


def test_si_queda_otra_persona_que_administra_la_baja_se_hace(
    central, norte, diego, activo, baja
):
    luis = _persona(central, "luis")
    afiliar_en(norte.pk, usuario_id=luis.pk, estado_id=activo.pk)
    darle_el_permiso(diego, norte.pk, activo.pk, LLAVE, PERMISO_DESAFILIAR)
    darle_el_permiso(luis, norte.pk, activo.pk, LLAVE, nombre_rol="Supervisor B")
    membresia = _membresia(luis, norte)

    resultado = _como(
        diego,
        norte.pk,
        DESAFILIAR,
        datos={"membresiaId": str(membresia.pk), "estadoBajaId": str(baja.pk)},
    )

    assert resultado.errors is None, resultado.errors
    assert _membresia(luis, norte).estado_id == baja.pk


def test_los_miembros_traen_solo_sus_roles_vigentes(central, norte, diego, activo):
    luis = _persona(central, "luis")
    marta = _persona(central, "marta")
    afiliar_en(norte.pk, usuario_id=luis.pk, estado_id=activo.pk)
    afiliar_en(norte.pk, usuario_id=marta.pk, estado_id=activo.pk)
    darle_el_permiso(diego, norte.pk, activo.pk, PERMISO_LISTAR)
    ayer = datetime.date.today() - datetime.timedelta(days=1)
    with empresa(norte.pk):
        suplente = seguridad.crear_rol(nombre="Suplente", estado_id=activo.pk)
        seguridad.asignar_rol(
            membresia_id=membresias.membresia_de(marta.pk).pk,
            grupo_id=suplente.pk,
            estado_id=activo.pk,
            fecha_inicio=ayer - datetime.timedelta(days=30),
            fecha_fin=ayer,
        )

    resultado = _como(
        diego, norte.pk, "{ miembros { usuario { username } roles { nombre } } }"
    )

    assert resultado.errors is None, resultado.errors
    roles = {
        miembro["usuario"]["username"]: sorted(rol["nombre"] for rol in miembro["roles"])
        for miembro in resultado.data["miembros"]
    }
    assert roles == {"diego": ["Administrador", "Supervisor"], "luis": [], "marta": []}
