import pytest
from django.core.exceptions import ValidationError

from comun.empresas import api as empresas
from core.tenancy import empresa as usar_empresa

pytestmark = pytest.mark.django_db


def test_agregar_un_segundo_pais(matriz, catalogo_empresas):
    empresas.agregar_pais(
        empresa_id=matriz.pk,
        pais_id=catalogo_empresas["peru"].pk,
        direccion="Av. Arequipa 100",
        telefono="+51 1 1234567",
    )

    paises = empresas.listar_paises_de(matriz.pk)
    assert len(paises) == 2


def test_no_se_repite_el_pais(matriz, catalogo_empresas):
    with pytest.raises(ValidationError, match="ya tiene una ficha para ese país"):
        empresas.agregar_pais(
            empresa_id=matriz.pk, pais_id=catalogo_empresas["bolivia"].pk
        )


def test_un_pais_inexistente_da_error_legible(matriz):
    with pytest.raises(ValidationError, match="No existe el país"):
        empresas.agregar_pais(empresa_id=matriz.pk, pais_id=99999)


def test_la_ubicacion_tiene_que_ser_del_pais_declarado(matriz, catalogo_empresas):
    from comun.geografia import api as geografia

    santa_cruz = geografia.crear_ubicacion(
        pais_id=catalogo_empresas["bolivia"].pk,
        nombre="Santa Cruz",
        tipo="Departamento",
        estado_id=catalogo_empresas["estado_activo"].pk,
    )

    with pytest.raises(ValidationError, match="no pertenece a ese país"):
        empresas.agregar_pais(
            empresa_id=matriz.pk,
            pais_id=catalogo_empresas["peru"].pk,
            ubicacion_geografica_id=santa_cruz.pk,
        )


def test_una_empresa_no_ve_los_paises_de_otra(matriz, datos_base, catalogo_empresas):
    from comun.empresas.models import EmpresaPais

    otra = empresas.crear_empresa(
        ident_tributaria="7654321", razon_social="Panadería La Espiga S.R.L.",
        **datos_base,
    )

    with usar_empresa(matriz.pk):
        visibles = list(EmpresaPais.objects.all())

    assert len(visibles) == 1
    assert visibles[0].empresa_id == matriz.pk
    assert all(f.empresa_id != otra.pk for f in visibles)


def test_la_ficha_nace_con_la_empresa_correcta(matriz, catalogo_empresas):
    fila = empresas.agregar_pais(
        empresa_id=matriz.pk, pais_id=catalogo_empresas["peru"].pk
    )

    assert fila.empresa_id == matriz.pk
