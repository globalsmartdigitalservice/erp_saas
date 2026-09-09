import pytest
from django.db import IntegrityError

from comun.empresas.models import EmpresaMoneda
from comun.monedas import api as monedas
from core.tenancy import SinEmpresaEnContexto, empresa, sin_filtro_de_empresa

pytestmark = pytest.mark.django_db


@pytest.fixture
def dolar(catalogo):
    """Una segunda moneda: la del catálogo ya la tiene cada empresa."""
    return monedas.crear_moneda(
        descripcion="Dólar estadounidense",
        codigo="USD",
        simbolo="$",
        estado_id=catalogo["estado_activo"].pk,
    )


def test_consultar_sin_empresa_revienta(empresa_a):
    with pytest.raises(SinEmpresaEnContexto):
        list(EmpresaMoneda.objects.all())


def test_cada_empresa_ve_solo_lo_suyo(empresa_a, empresa_b):
    with empresa(empresa_a.id):
        de_a = list(EmpresaMoneda.objects.all())

    with empresa(empresa_b.id):
        de_b = list(EmpresaMoneda.objects.all())

    assert [f.empresa_id for f in de_a] == [empresa_a.id]
    assert [f.empresa_id for f in de_b] == [empresa_b.id]


def test_no_se_puede_leer_por_id_una_fila_ajena(empresa_a, empresa_b):
    with empresa(empresa_b.id):
        ajena = EmpresaMoneda.objects.first()

    with empresa(empresa_a.id):
        with pytest.raises(EmpresaMoneda.DoesNotExist):
            EmpresaMoneda.objects.get(pk=ajena.pk)


def test_sin_filtro_de_empresa_ve_todo(empresa_a, empresa_b):
    with sin_filtro_de_empresa():
        assert EmpresaMoneda.objects.count() == 2


def test_al_guardar_la_empresa_se_rellena_sola(empresa_a, dolar, catalogo):
    with empresa(empresa_a.id):
        fila = EmpresaMoneda(moneda=dolar, estado=catalogo["estado_activo"])
        fila.save()

    assert fila.empresa_id == empresa_a.id


def test_guardar_sin_empresa_no_inventa_una(empresa_a, dolar, catalogo):
    with pytest.raises((IntegrityError, SinEmpresaEnContexto)):
        EmpresaMoneda(moneda=dolar, estado=catalogo["estado_activo"]).save()
