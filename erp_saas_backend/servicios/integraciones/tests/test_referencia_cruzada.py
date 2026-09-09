import pytest
from django.core.exceptions import ValidationError

from comun.catalogo_modulos import api as modulos
from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa
from servicios.integraciones import api as integraciones

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogo_vinculos(catalogo):
    """Los módulos y el tipo de vínculo que hacen falta para vincular algo."""
    modulos.crear(
        codigo="VENTAS", nombre="Ventas", estado_id=catalogo["estado_activo"].pk
    )
    modulos.crear(
        codigo="COMPRAS", nombre="Compras", estado_id=catalogo["estado_activo"].pk
    )

    return {
        **catalogo,
        "genera": catalogo["tipologia"](AGRUPADOR.TIPO_VINCULO, "GENERA"),
    }


@pytest.fixture
def vincular(catalogo_vinculos):
    """Fábrica con los valores del caso típico ya puestos."""

    def _vincular(**extra):
        campos = {
            "modulo_origen": "VENTAS",
            "tabla_origen": "vent_pedido",
            "registro_origen_id": 7,
            "modulo_destino": "VENTAS",
            "tabla_destino": "vent_documento",
            "registro_destino_id": 12,
            "tipo_vinculo_id": catalogo_vinculos["genera"].pk,
            "estado_id": catalogo_vinculos["estado_activo"].pk,
        }
        campos.update(extra)
        return integraciones.vincular(**campos)

    return _vincular


def test_el_vinculo_se_navega_para_los_dos_lados(empresa_a, vincular):
    with empresa(empresa_a.id):
        vincular()

        adelante = integraciones.que_genero("vent_pedido", 7)
        atras = integraciones.de_donde_viene("vent_documento", 12)

    assert len(adelante) == 1
    assert adelante[0].tabla_destino == "vent_documento"

    assert len(atras) == 1
    assert atras[0].tabla_origen == "vent_pedido"


def test_el_vinculo_es_dirigido(empresa_a, vincular):
    with empresa(empresa_a.id):
        vincular()

        assert integraciones.que_genero("vent_documento", 12) == []
        assert integraciones.de_donde_viene("vent_pedido", 7) == []


def test_un_registro_puede_generar_varios(empresa_a, vincular):
    with empresa(empresa_a.id):
        vincular()
        vincular(tabla_destino="vent_documento", registro_destino_id=13)

        assert len(integraciones.que_genero("vent_pedido", 7)) == 2


def test_los_vinculos_de_otra_empresa_no_se_ven(empresa_a, empresa_b, vincular):
    with empresa(empresa_a.id):
        vincular()

    with empresa(empresa_b.id):
        assert integraciones.que_genero("vent_pedido", 7) == []
        assert integraciones.de_donde_viene("vent_documento", 12) == []


def test_un_modulo_que_no_existe_se_rechaza(empresa_a, vincular):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="No existe el módulo"):
            vincular(modulo_origen="INVENTARIO")


def test_el_codigo_de_modulo_se_normaliza(empresa_a, vincular):
    with empresa(empresa_a.id):
        fila = vincular(modulo_origen="  ventas  ")

    assert fila.modulo_origen == "VENTAS"


def test_un_registro_no_se_vincula_consigo_mismo(empresa_a, vincular):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="consigo mismo"):
            vincular(tabla_destino="vent_pedido", registro_destino_id=7)


def test_la_misma_tabla_con_otro_id_si_se_vincula(empresa_a, vincular):
    with empresa(empresa_a.id):
        fila = vincular(tabla_destino="vent_pedido", registro_destino_id=8)

    assert fila.pk is not None


def test_el_mismo_vinculo_no_se_repite(empresa_a, vincular):
    with empresa(empresa_a.id):
        vincular()

        with pytest.raises(ValidationError, match="ya está registrado"):
            vincular()


def test_un_tipo_de_vinculo_de_otra_lista_se_rechaza(
    empresa_a, vincular, catalogo_vinculos
):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Se esperaba un tipo de vínculo"):
            vincular(tipo_vinculo_id=catalogo_vinculos["estado_activo"].pk)


def test_anular_es_soft_delete(empresa_a, vincular, catalogo_vinculos):
    baja = catalogo_vinculos["tipologia"](AGRUPADOR.ESTADO_REGISTRO, "BAJA")

    with empresa(empresa_a.id):
        fila = vincular()
        anulada = integraciones.anular(fila.pk)

        assert integraciones.obtener(fila.pk) is not None

    assert anulada.estado_id == baja.pk
