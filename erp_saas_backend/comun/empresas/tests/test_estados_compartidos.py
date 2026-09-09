import pytest

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR

pytestmark = pytest.mark.django_db


def test_un_pais_y_una_moneda_usan_LA_MISMA_fila(catalogo_empresas):
    assert (
        catalogo_empresas["bolivia"].estado_id
        == catalogo_empresas["moneda"].estado_id
        == catalogo_empresas["estado_activo"].pk
    )


def test_esa_fila_es_del_agrupador_compartido(catalogo_empresas):
    compartida = catalogo_empresas["estado_activo"]

    assert compartida.agrupador == AGRUPADOR.ESTADO_REGISTRO
    assert tipologias.es_del_agrupador(compartida.pk, AGRUPADOR.ESTADO_REGISTRO)


def test_la_empresa_NO_comparte_esa_lista(catalogo_empresas):
    activa = catalogo_empresas["activa"]

    assert activa.agrupador == AGRUPADOR.ESTADO_EMPRESA
    assert activa.pk != catalogo_empresas["estado_activo"].pk
