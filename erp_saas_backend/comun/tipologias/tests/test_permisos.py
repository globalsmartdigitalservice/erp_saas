import pytest
from django.core.exceptions import ValidationError

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa

pytestmark = pytest.mark.django_db


def test_sin_fila_no_se_puede_ampliar(empresa_a):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="no puede agregar valores propios"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_con_fila_si_se_puede(empresa_a, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_a.id):
        fila = tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")

    assert fila.empresa_id == empresa_a.id


def test_el_permiso_es_POR_LISTA_no_general(empresa_a, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_a.id):
        tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")

        with pytest.raises(ValidationError, match="no puede agregar valores propios"):
            tipologias.crear(agrupador=AGRUPADOR.TIPO_EMPRESA, nombre="Cooperativa")


def test_el_permiso_no_cruza_empresas(empresa_a, empresa_b, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_b.id):
        with pytest.raises(ValidationError, match="no puede agregar valores propios"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_un_agrupador_inexistente_falla_antes_que_el_permiso(empresa_a):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="agrupador 999 no existe"):
            tipologias.crear(agrupador=999, nombre="Fantasma")


def test_sin_empresa_falla_antes_que_el_permiso(db):
    with pytest.raises(ValidationError, match="No hay empresa en el contexto"):
        tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_habilitar_es_idempotente(empresa_a):
    tipologias.habilitar_agrupador(empresa_a.id, AGRUPADOR.RUBRO)
    tipologias.habilitar_agrupador(empresa_a.id, AGRUPADOR.RUBRO)

    assert tipologias.agrupadores_ampliables_de(empresa_a.id) == [AGRUPADOR.RUBRO]


def test_deshabilitar_revoca(empresa_a):
    tipologias.habilitar_agrupador(empresa_a.id, AGRUPADOR.RUBRO)
    tipologias.deshabilitar_agrupador(empresa_a.id, AGRUPADOR.RUBRO)

    assert tipologias.agrupadores_ampliables_de(empresa_a.id) == []

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="no puede agregar valores propios"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_no_se_habilita_una_lista_que_no_existe(empresa_a):
    with pytest.raises(ValidationError, match="agrupador 999 no existe"):
        tipologias.habilitar_agrupador(empresa_a.id, 999)


def test_no_se_habilita_para_una_empresa_que_no_existe(db):
    with pytest.raises(ValidationError, match="No existe la empresa"):
        tipologias.habilitar_agrupador(99999, AGRUPADOR.RUBRO)


def test_puede_ampliar_usa_la_empresa_del_contexto(empresa_a, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_a.id):
        assert tipologias.puede_ampliar(AGRUPADOR.RUBRO) is True
        assert tipologias.puede_ampliar(AGRUPADOR.TIPO_EMPRESA) is False


def test_puede_ampliar_sin_contexto_es_false(db):
    assert tipologias.puede_ampliar(AGRUPADOR.RUBRO) is False
