import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from comun.membresias import api as membresias
from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa

pytestmark = pytest.mark.django_db

Usuario = get_user_model()


@pytest.fixture
def juan(empresa_a):
    return Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def de_baja(catalogo):
    return catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, "BAJA")


@pytest.fixture
def cadena(crear_empresa, empresa_a):
    """La empresa de Juan con dos sucursales.

    Cuelga de `empresa_a` y no de una matriz aparte: una cuenta solo
    trabaja en empresas de SU cliente, así que si la cadena fuera otro
    cliente, Juan no podría entrar a ninguna de las tres."""
    norte = crear_empresa("Sucursal Norte", padre=empresa_a)
    sur = crear_empresa("Sucursal Sur", padre=empresa_a)
    return empresa_a, norte, sur


def empresas_donde_esta(usuario) -> set[int]:
    """Ayuda de lectura: los ids de las empresas donde está afiliado."""
    return {m.empresa_id for m in membresias.empresas_de(usuario.id)}


def test_afiliar(juan, empresa_a, activo):
    m = membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )

    assert m.usuario_id == juan.id
    assert m.empresa_id == empresa_a.id
    assert m.fecha_finalizacion is None


def test_no_se_afilia_dos_veces_a_la_misma_empresa(juan, empresa_a, activo):
    membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )

    with pytest.raises(ValidationError, match="ya está dado de alta"):
        membresias.afiliar(
            usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
        )


def test_no_se_afilia_un_usuario_dado_de_baja(juan, empresa_a, activo):
    juan.is_active = False
    juan.save(update_fields=["is_active"])

    with pytest.raises(ValidationError, match="dado de baja del sistema"):
        membresias.afiliar(
            usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
        )


def test_el_estado_tiene_que_ser_del_agrupador_correcto(juan, empresa_a, catalogo):
    with pytest.raises(ValidationError, match="Se esperaba un estado de membresía"):
        membresias.afiliar(
            usuario_id=juan.id,
            empresa_id=empresa_a.id,
            estado_id=catalogo["rubro"].id,
        )


def test_no_se_afilia_a_una_empresa_que_no_existe(juan, activo):
    # El texto es el mismo que para una empresa ajena, a propósito: ver
    # `test_el_rechazo_no_delata_si_la_empresa_existe`.
    with pytest.raises(ValidationError, match="no está disponible"):
        membresias.afiliar(usuario_id=juan.id, empresa_id=999999, estado_id=activo.id)


def test_afiliar_al_grupo_da_de_alta_en_la_matriz_y_sus_sucursales(
    juan, cadena, activo
):
    matriz, norte, sur = cadena

    creadas = membresias.afiliar_al_grupo(
        usuario_id=juan.id, empresa_id=matriz.id, estado_id=activo.id
    )

    assert {m.empresa_id for m in creadas} == {matriz.id, norte.id, sur.id}


def test_afiliar_al_grupo_no_toca_a_otro_cliente(juan, cadena, empresa_b, activo):
    matriz, _, _ = cadena

    membresias.afiliar_al_grupo(
        usuario_id=juan.id, empresa_id=matriz.id, estado_id=activo.id
    )

    assert empresa_b.id not in empresas_donde_esta(juan)


def test_afiliar_al_grupo_saltea_donde_ya_estaba(juan, cadena, activo):
    matriz, norte, sur = cadena
    membresias.afiliar(usuario_id=juan.id, empresa_id=norte.id, estado_id=activo.id)

    creadas = membresias.afiliar_al_grupo(
        usuario_id=juan.id, empresa_id=matriz.id, estado_id=activo.id
    )

    assert {m.empresa_id for m in creadas} == {matriz.id, sur.id}
    assert empresas_donde_esta(juan) == {matriz.id, norte.id, sur.id}


def test_afiliar_al_grupo_desde_una_sucursal_solo_la_afilia_a_ella(
    juan, cadena, activo
):
    matriz, norte, _ = cadena

    creadas = membresias.afiliar_al_grupo(
        usuario_id=juan.id, empresa_id=norte.id, estado_id=activo.id
    )

    assert [m.empresa_id for m in creadas] == [norte.id]
    assert matriz.id not in empresas_donde_esta(juan)


def test_afiliar_al_grupo_no_deja_un_alta_a_medias(juan, cadena, catalogo):
    matriz, _, _ = cadena

    with pytest.raises(ValidationError):
        membresias.afiliar_al_grupo(
            usuario_id=juan.id, empresa_id=matriz.id, estado_id=catalogo["rubro"].id
        )

    assert empresas_donde_esta(juan) == set()


def test_empresas_de_funciona_sin_empresa_en_el_contexto(juan, cadena, activo):
    matriz, norte, sur = cadena
    membresias.afiliar_al_grupo(
        usuario_id=juan.id, empresa_id=matriz.id, estado_id=activo.id
    )

    assert empresas_donde_esta(juan) == {matriz.id, norte.id, sur.id}


def test_listar_solo_muestra_a_los_de_la_empresa_del_contexto(juan, cadena, activo):
    matriz, norte, _ = cadena
    ana = Usuario.objects.create_user(
        username="ana",
        email="ana@acme.com",
        password="Zq4tRn8Vd3",
        matriz=matriz,
    )
    membresias.afiliar(usuario_id=juan.id, empresa_id=matriz.id, estado_id=activo.id)
    membresias.afiliar(usuario_id=ana.id, empresa_id=norte.id, estado_id=activo.id)

    with empresa(matriz.id):
        assert [m.usuario_id for m in membresias.listar_membresias()] == [juan.id]


def test_desafiliar_no_borra_la_fila(juan, empresa_a, activo, de_baja):
    m = membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )

    with empresa(empresa_a.id):
        baja = membresias.desafiliar(membresia_id=m.id, estado_baja_id=de_baja.id)

    assert baja.id == m.id
    assert baja.estado_id == de_baja.id
    assert baja.fecha_finalizacion == datetime.date.today()


def test_desafiliar_de_una_empresa_no_afecta_a_las_otras(
    juan, cadena, activo, de_baja
):
    matriz, norte, sur = cadena
    membresias.afiliar_al_grupo(
        usuario_id=juan.id, empresa_id=matriz.id, estado_id=activo.id
    )
    la_de_norte = next(
        m for m in membresias.empresas_de(juan.id) if m.empresa_id == norte.id
    )

    with empresa(norte.id):
        membresias.desafiliar(membresia_id=la_de_norte.id, estado_baja_id=de_baja.id)

    activas = {
        m.empresa_id
        for m in membresias.empresas_de(juan.id)
        if m.estado_id == activo.id
    }
    assert activas == {matriz.id, sur.id}


def test_el_que_vuelve_reactiva_su_fila(juan, empresa_a, activo, de_baja):
    m = membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )

    with empresa(empresa_a.id):
        membresias.desafiliar(membresia_id=m.id, estado_baja_id=de_baja.id)
        vuelta = membresias.reactivar(membresia_id=m.id, estado_activo_id=activo.id)

    assert vuelta.id == m.id
    assert vuelta.fecha_finalizacion is None
    assert vuelta.estado_id == activo.id


def test_no_se_afilia_a_la_empresa_de_OTRO_cliente(juan, empresa_b, activo):
    """El agujero: el administrador de un cliente metía a su gente —o a la
    ajena— en la empresa de otro, y desde ahí le veía las ventas."""
    with pytest.raises(ValidationError, match="no está disponible"):
        membresias.afiliar(
            usuario_id=juan.id, empresa_id=empresa_b.id, estado_id=activo.id
        )


def test_el_rechazo_no_delata_si_la_empresa_existe(juan, empresa_b, activo):
    """Un mensaje distinto para 'no existe' y para 'no es tuya' deja armar
    el padrón de empresas probando números."""
    with pytest.raises(ValidationError) as ajena:
        membresias.afiliar(
            usuario_id=juan.id, empresa_id=empresa_b.id, estado_id=activo.id
        )

    with pytest.raises(ValidationError) as inexistente:
        membresias.afiliar(
            usuario_id=juan.id, empresa_id=999999, estado_id=activo.id
        )

    assert ajena.value.messages == inexistente.value.messages


def test_SI_se_afilia_a_una_sucursal_del_mismo_cliente(juan, empresa_a, crear_empresa, activo):
    """Lo que tiene que seguir funcionando: el grupo del propio cliente."""
    sucursal = crear_empresa("Sucursal Norte", padre=empresa_a)

    membresia = membresias.afiliar(
        usuario_id=juan.id, empresa_id=sucursal.id, estado_id=activo.id
    )

    assert membresia.empresa_id == sucursal.id
