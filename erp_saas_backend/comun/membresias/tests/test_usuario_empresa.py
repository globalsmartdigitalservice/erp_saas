import datetime

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from comun.membresias.models import UsuarioEmpresa
from core.tenancy import SinEmpresaEnContexto, empresa, sin_filtro_de_empresa

pytestmark = pytest.mark.django_db

Usuario = get_user_model()
HOY = datetime.date(2026, 9, 7)


@pytest.fixture
def juan():
    return Usuario.objects.create_user(
        username="juan", email="juan@acme.com", password="Kx7pLm9Qw2"
    )


@pytest.fixture
def afiliar(catalogo):
    """Mete a una persona en una empresa, saltando el filtro a propósito."""

    def _afiliar(usuario, la_empresa, fecha=HOY):
        with sin_filtro_de_empresa():
            return UsuarioEmpresa.objects.create(
                usuario=usuario,
                empresa=la_empresa,
                fecha_asignacion=fecha,
                estado=catalogo["estado_activo"],
            )

    return _afiliar


def test_la_misma_persona_puede_estar_en_dos_empresas(juan, empresa_a, empresa_b, afiliar):
    afiliar(juan, empresa_a)
    afiliar(juan, empresa_b)

    with sin_filtro_de_empresa():
        assert UsuarioEmpresa.objects.filter(usuario=juan).count() == 2


def test_no_se_puede_afiliar_dos_veces_a_la_misma_empresa(juan, empresa_a, afiliar):
    afiliar(juan, empresa_a)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            afiliar(juan, empresa_a)


def test_sin_empresa_en_el_contexto_la_consulta_normal_revienta(juan, empresa_a, afiliar):
    afiliar(juan, empresa_a)

    with pytest.raises(SinEmpresaEnContexto):
        list(UsuarioEmpresa.objects.filter(usuario=juan))


def test_el_login_encuentra_las_membresias_con_la_puerta_de_salida(
    juan, empresa_a, empresa_b, afiliar
):
    afiliar(juan, empresa_a)
    afiliar(juan, empresa_b)

    with sin_filtro_de_empresa():
        empresas = {m.empresa_id for m in UsuarioEmpresa.objects.filter(usuario=juan)}

    assert empresas == {empresa_a.id, empresa_b.id}


def test_elegida_la_empresa_solo_se_ve_la_de_ella(juan, empresa_a, empresa_b, afiliar):
    afiliar(juan, empresa_a)
    afiliar(juan, empresa_b)

    with empresa(empresa_a.id):
        membresias = list(UsuarioEmpresa.objects.filter(usuario=juan))

    assert len(membresias) == 1
    assert membresias[0].empresa_id == empresa_a.id


def test_una_empresa_no_ve_a_los_empleados_de_la_otra(
    juan, empresa_a, empresa_b, afiliar, catalogo
):
    ana = Usuario.objects.create_user(
        username="ana", email="ana@otra.com", password="Zq4tRn8Vd3"
    )
    afiliar(juan, empresa_a)
    afiliar(ana, empresa_b)

    with empresa(empresa_a.id):
        usuarios = {m.usuario_id for m in UsuarioEmpresa.objects.all()}

    assert usuarios == {juan.id}


def test_la_membresia_vigente_no_tiene_fecha_de_finalizacion(juan, empresa_a, afiliar):
    membresia = afiliar(juan, empresa_a)

    assert membresia.fecha_finalizacion is None


def test_el_usuario_no_se_puede_borrar_si_tiene_membresias(juan, empresa_a, afiliar):
    from django.db.models import ProtectedError

    afiliar(juan, empresa_a)

    with pytest.raises(ProtectedError):
        juan.delete()
