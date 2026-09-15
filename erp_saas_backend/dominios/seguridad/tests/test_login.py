import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from comun.membresias import api as membresias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ACCESO_BLOQUEADO,
    NOMBRE_ACCESO_EXITO,
    NOMBRE_ACCESO_FALLO,
)
from core.tenancy import empresa, sin_filtro_de_empresa
from dominios.seguridad import api as seguridad
from dominios.seguridad import tokens
from dominios.seguridad.models import SesionAcceso
from dominios.seguridad.services import login
from core.tests.afiliacion import afiliar_en

pytestmark = pytest.mark.django_db

Usuario = get_user_model()
LUNES = datetime.date(2026, 9, 7)


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def resultados(catalogo):
    """Las tres filas de RESULTADO_ACCESO que la semilla carga."""
    return {
        nombre: catalogo["tipologia"](AGRUPADOR.RESULTADO_ACCESO, nombre)
        for nombre in (
            NOMBRE_ACCESO_EXITO,
            NOMBRE_ACCESO_BLOQUEADO,
            NOMBRE_ACCESO_FALLO,
        )
    }


@pytest.fixture
def juan(empresa_a):
    return Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )


@pytest.fixture
def en_gimnasio(juan, empresa_a, activo, resultados):
    return afiliar_en(empresa_a.id, usuario_id=juan.id, estado_id=activo.id)


@pytest.fixture
def en_dos_empresas(juan, en_gimnasio, sucursal_a, activo):
    """En la matriz y en su sucursal: el gerente de la cadena."""
    afiliar_en(sucursal_a.id, usuario_id=juan.id, estado_id=activo.id)
    return en_gimnasio


def test_un_usuario_que_no_existe_da_el_mismo_mensaje_que_una_clave_mala(
    en_gimnasio,
):
    with pytest.raises(ValidationError) as inexistente:
        login.login(identificador="nadie@acme.com", password="Kx7pLm9Qw2")

    with pytest.raises(ValidationError) as clave_mala:
        login.login(identificador="juan@acme.com", password="otra cosa")

    assert inexistente.value.messages == clave_mala.value.messages
    assert inexistente.value.messages == [login.CREDENCIALES_INVALIDAS]


def test_un_usuario_dado_de_baja_da_el_mismo_mensaje(juan, en_gimnasio):
    juan.is_active = False
    juan.save(update_fields=["is_active"])

    with pytest.raises(ValidationError) as error:
        login.login(identificador="juan", password="Kx7pLm9Qw2")

    assert error.value.messages == [login.CREDENCIALES_INVALIDAS]


def test_una_empresa_ajena_da_el_mismo_mensaje_que_una_inexistente(
    en_gimnasio, empresa_b
):
    with pytest.raises(ValidationError) as ajena:
        login.login(
            identificador="juan", password="Kx7pLm9Qw2", empresa_id=empresa_b.id
        )

    with pytest.raises(ValidationError) as inexistente:
        login.login(
            identificador="juan", password="Kx7pLm9Qw2", empresa_id=999999
        )

    assert ajena.value.messages == inexistente.value.messages


def test_con_una_sola_empresa_entra_directo(en_gimnasio, empresa_a):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")

    assert not resultado.necesita_elegir_empresa
    assert resultado.acceso and resultado.refresh
    assert tokens.leer(resultado.acceso, tipo=tokens.TIPO_ACCESO)["emp"] == empresa_a.id


def test_entra_por_correo(en_gimnasio):
    assert login.login(
        identificador="juan@acme.com", password="Kx7pLm9Qw2"
    ).acceso


def test_con_varias_empresas_devuelve_la_lista_y_NO_un_token(
    en_dos_empresas, empresa_a, sucursal_a
):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")

    assert resultado.necesita_elegir_empresa
    assert resultado.acceso == ""
    assert {m.empresa_id for m in resultado.empresas} == {empresa_a.id, sucursal_a.id}


def test_elegir_empresa_devuelve_el_token_de_esa_empresa(
    en_dos_empresas, sucursal_a
):
    resultado = login.elegir_empresa(
        identificador="juan", password="Kx7pLm9Qw2", empresa_id=sucursal_a.id
    )

    assert tokens.leer(resultado.acceso, tipo=tokens.TIPO_ACCESO)["emp"] == sucursal_a.id


def test_sin_ninguna_empresa_no_entra(juan, resultados):
    with pytest.raises(ValidationError, match="no está habilitado"):
        login.login(identificador="juan", password="Kx7pLm9Qw2")


def test_el_ingreso_queda_registrado(en_gimnasio, empresa_a, resultados):
    login.login(identificador="juan", password="Kx7pLm9Qw2")

    with empresa(empresa_a.id):
        sesion = SesionAcceso.objects.first()

    assert sesion.resultado_id == resultados[NOMBRE_ACCESO_EXITO].id
    assert sesion.esta_abierta


def test_el_rechazo_por_horario_TAMBIEN_queda_registrado(
    en_gimnasio, empresa_a, activo, resultados
):
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,
            hora_inicio=datetime.time(8, 0),
            hora_fin=datetime.time(12, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )

    with pytest.raises(ValidationError, match="Fuera del horario"):
        login.login(
            identificador="juan",
            password="Kx7pLm9Qw2",
            momento=datetime.datetime.combine(LUNES, datetime.time(20, 0)),
        )

    with empresa(empresa_a.id):
        sesion = SesionAcceso.objects.first()

    assert sesion.resultado_id == resultados[NOMBRE_ACCESO_BLOQUEADO].id
    # Una sesión rechazada NUNCA estuvo abierta: sin `fin` se contaría
    # como activa para siempre.
    assert not sesion.esta_abierta


def test_otra_empresa_no_ve_los_accesos(
    en_dos_empresas, empresa_a, sucursal_a, resultados
):
    login.elegir_empresa(
        identificador="juan", password="Kx7pLm9Qw2", empresa_id=empresa_a.id
    )

    with empresa(sucursal_a.id):
        assert SesionAcceso.objects.count() == 0


def test_despues_de_salir_el_refresh_ya_no_sirve(en_gimnasio, resultados):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")

    login.logout(sesion_id=resultado.sesion.pk)

    with pytest.raises(ValidationError, match="venció"):
        login.refresh(token=resultado.refresh)


def test_salir_dos_veces_no_falla(en_gimnasio, resultados):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")

    login.logout(sesion_id=resultado.sesion.pk)
    assert login.logout(sesion_id=resultado.sesion.pk) is not None


def test_renovar_devuelve_tokens_nuevos(en_gimnasio, resultados):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")

    renovado = login.refresh(token=resultado.refresh)

    assert renovado.acceso
    assert renovado.refresh != resultado.refresh


def test_el_refresh_viejo_deja_de_servir(en_gimnasio, resultados):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")
    login.refresh(token=resultado.refresh)

    with pytest.raises(ValidationError, match="venció"):
        login.refresh(token=resultado.refresh)


def test_un_token_de_acceso_no_sirve_para_renovar(en_gimnasio, resultados):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")

    with pytest.raises(ValidationError, match="venció"):
        login.refresh(token=resultado.acceso)


def test_un_token_firmado_con_otra_clave_no_sirve(en_gimnasio, resultados):
    import jwt as pyjwt

    falso = pyjwt.encode(
        {"typ": tokens.TIPO_REFRESH, "sub": "1", "emp": 1, "ses": 1, "jti": "x"},
        "otra clave cualquiera",
        algorithm="HS256",
    )

    with pytest.raises(ValidationError, match="venció"):
        login.refresh(token=falso)


def test_el_usuario_dado_de_baja_no_puede_renovar(juan, en_gimnasio, resultados):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")
    juan.is_active = False
    juan.save(update_fields=["is_active"])

    with pytest.raises(ValidationError, match="venció"):
        login.refresh(token=resultado.refresh)


def test_todos_los_fallos_de_renovacion_dicen_lo_mismo(en_gimnasio, resultados):
    resultado = login.login(identificador="juan", password="Kx7pLm9Qw2")
    login.logout(sesion_id=resultado.sesion.pk)

    mensajes = []
    for token in (resultado.refresh, resultado.acceso, "esto no es un token"):
        with pytest.raises(ValidationError) as error:
            login.refresh(token=token)
        mensajes.append(error.value.messages)

    assert len(set(map(tuple, mensajes))) == 1


class RequestFalso:
    def __init__(self, **meta):
        self.META = meta


def test_sin_proxy_el_header_se_ignora(settings):
    from core.red import ip_del_cliente

    settings.PROXIES_CONFIABLES = 0
    request = RequestFalso(
        REMOTE_ADDR="10.0.0.5", HTTP_X_FORWARDED_FOR="1.2.3.4"
    )

    assert ip_del_cliente(request) == "10.0.0.5"


def test_con_un_proxy_se_lee_desde_la_derecha(settings):
    from core.red import ip_del_cliente

    settings.PROXIES_CONFIABLES = 1
    request = RequestFalso(
        REMOTE_ADDR="10.0.0.5",
        HTTP_X_FORWARDED_FOR="1.2.3.4, 190.104.1.10",
    )

    assert ip_del_cliente(request) == "190.104.1.10"


def test_si_llegan_menos_entradas_de_las_esperadas_no_se_adivina(settings):
    from core.red import ip_del_cliente

    settings.PROXIES_CONFIABLES = 3
    request = RequestFalso(
        REMOTE_ADDR="10.0.0.5", HTTP_X_FORWARDED_FOR="1.2.3.4"
    )

    assert ip_del_cliente(request) == "10.0.0.5"


def test_la_ip_queda_en_el_registro_del_acceso(
    en_gimnasio, empresa_a, resultados, settings
):
    settings.PROXIES_CONFIABLES = 1
    request = RequestFalso(
        REMOTE_ADDR="10.0.0.5",
        HTTP_X_FORWARDED_FOR="1.2.3.4, 190.104.1.10",
        HTTP_USER_AGENT="Mozilla/5.0",
    )

    login.login(
        identificador="juan", password="Kx7pLm9Qw2", request=request
    )

    with empresa(empresa_a.id):
        sesion = SesionAcceso.objects.first()

    assert sesion.ip == "190.104.1.10"
    assert sesion.user_agent == "Mozilla/5.0"
