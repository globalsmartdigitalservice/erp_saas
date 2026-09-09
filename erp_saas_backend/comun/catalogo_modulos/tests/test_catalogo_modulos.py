import pytest
from django.core.exceptions import ValidationError

from comun.catalogo_modulos import api as modulos
from comun.catalogo_modulos.models import ModuloDependencia
from comun.tipologias.constantes import AGRUPADOR

pytestmark = pytest.mark.django_db


@pytest.fixture
def crear_modulo(catalogo):
    """Fábrica: `crear_modulo("VENTAS", vendible=True)`."""

    def _crear(codigo, vendible=False):
        return modulos.crear(
            codigo=codigo,
            nombre=codigo.title(),
            estado_id=catalogo["estado_activo"].pk,
            es_vendible=vendible,
        )

    return _crear


def test_es_vendible_separa_lo_que_se_cobra_de_lo_que_va_incluido(crear_modulo):
    crear_modulo("FARMACIA", vendible=True)
    crear_modulo("CATALOGO")

    assert [m.codigo for m in modulos.listar(solo_vendibles=True)] == ["FARMACIA"]
    assert len(modulos.listar()) == 2


def test_el_codigo_se_normaliza_y_no_se_repite(crear_modulo, catalogo):
    crear_modulo("ventas")

    assert modulos.obtener_por_codigo("VENTAS") is not None

    with pytest.raises(ValidationError, match="VENTAS"):
        modulos.crear(
            codigo="  ventas ",
            nombre="Otra vez",
            estado_id=catalogo["estado_activo"].pk,
        )


def test_no_es_un_catalogo_por_empresa(crear_modulo, empresa_a, empresa_b):
    from core.tenancy import empresa

    crear_modulo("VENTAS")

    with empresa(empresa_a.id):
        assert len(modulos.listar()) == 1
    with empresa(empresa_b.id):
        assert len(modulos.listar()) == 1


def test_la_cadena_llega_hasta_el_fondo(crear_modulo):
    """Si `cadena_de()` devolviera solo lo directo, faltaría instalar el
    último de la cadena sin que nada avise."""
    farmacia = crear_modulo("FARMACIA", vendible=True)
    inventario = crear_modulo("INVENTARIO")
    catalogo_base = crear_modulo("CATALOGO")

    modulos.declarar_dependencia(
        modulo_id=farmacia.pk, depende_de_id=inventario.pk
    )
    modulos.declarar_dependencia(
        modulo_id=inventario.pk, depende_de_id=catalogo_base.pk
    )

    assert sorted(modulos.cadena_de(farmacia.pk)) == sorted(
        [inventario.pk, catalogo_base.pk]
    )
    assert modulos.cadena_de(catalogo_base.pk) == []


def test_un_ciclo_se_rechaza(crear_modulo):
    a = crear_modulo("A")
    b = crear_modulo("B")

    modulos.declarar_dependencia(modulo_id=a.pk, depende_de_id=b.pk)

    with pytest.raises(ValidationError, match="ciclo"):
        modulos.declarar_dependencia(modulo_id=b.pk, depende_de_id=a.pk)


def test_un_ciclo_largo_tambien_se_rechaza(crear_modulo):
    a = crear_modulo("A")
    b = crear_modulo("B")
    c = crear_modulo("C")

    modulos.declarar_dependencia(modulo_id=a.pk, depende_de_id=b.pk)
    modulos.declarar_dependencia(modulo_id=b.pk, depende_de_id=c.pk)

    with pytest.raises(ValidationError, match="ciclo"):
        modulos.declarar_dependencia(modulo_id=c.pk, depende_de_id=a.pk)


def test_un_modulo_no_depende_de_si_mismo(crear_modulo):
    a = crear_modulo("A")

    with pytest.raises(ValidationError, match="de sí mismo"):
        modulos.declarar_dependencia(modulo_id=a.pk, depende_de_id=a.pk)


def test_la_dependencia_no_se_declara_dos_veces(crear_modulo):
    a = crear_modulo("A")
    b = crear_modulo("B")

    modulos.declarar_dependencia(modulo_id=a.pk, depende_de_id=b.pk)

    with pytest.raises(ValidationError, match="ya está declarada"):
        modulos.declarar_dependencia(modulo_id=a.pk, depende_de_id=b.pk)


def test_dura_y_suave_se_guardan_distinto(crear_modulo):
    a = crear_modulo("A")
    b = crear_modulo("B")
    c = crear_modulo("C")

    dura = modulos.declarar_dependencia(modulo_id=a.pk, depende_de_id=b.pk)
    suave = modulos.declarar_dependencia(
        modulo_id=a.pk, depende_de_id=c.pk, tipo=ModuloDependencia.Tipo.SUAVE
    )

    assert dura.tipo == "DURA"
    assert suave.tipo == "SUAVE"


def test_no_se_da_de_baja_un_modulo_del_que_otros_dependen(crear_modulo):
    farmacia = crear_modulo("FARMACIA", vendible=True)
    inventario = crear_modulo("INVENTARIO")

    modulos.declarar_dependencia(
        modulo_id=farmacia.pk, depende_de_id=inventario.pk
    )

    with pytest.raises(ValidationError, match="FARMACIA"):
        modulos.desactivar(inventario.pk)


def test_al_quitar_la_dependencia_ya_se_puede_dar_de_baja(crear_modulo, catalogo):
    farmacia = crear_modulo("FARMACIA")
    inventario = crear_modulo("INVENTARIO")

    modulos.declarar_dependencia(
        modulo_id=farmacia.pk, depende_de_id=inventario.pk
    )
    modulos.quitar_dependencia(farmacia.pk, inventario.pk)

    baja = catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, "BAJA")
    assert modulos.desactivar(inventario.pk).estado_id == baja.pk
