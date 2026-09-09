import pytest
from django.core.exceptions import ValidationError

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from comun.tipologias.models import Tipologia
from core.tenancy import empresa

pytestmark = pytest.mark.django_db


def test_crear_pone_la_empresa_del_contexto(empresa_a, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_a.id):
        fila = tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")

    assert fila.empresa_id == empresa_a.id


def test_crear_sin_empresa_no_ensucia_el_catalogo_del_sistema(db):
    with pytest.raises(ValidationError, match="No hay empresa en el contexto"):
        tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_el_input_de_graphql_no_expone_la_empresa():
    from config.schema import schema

    campos = {
        campo.name
        for campo in schema.schema_converter.type_map[
            "CrearTipologiaInput"
        ].definition.fields
    }

    assert "empresa" not in campos
    assert "empresa_id" not in campos


def test_la_empresa_ve_la_del_sistema(empresa_a, rubro_del_sistema):
    with empresa(empresa_a.id):
        assert tipologias.obtener(rubro_del_sistema.pk) is not None


def test_pero_no_la_puede_modificar(empresa_a, rubro_del_sistema):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="catálogo del sistema"):
            tipologias.actualizar(rubro_del_sistema.pk, nombre="Farmacia")


def test_ni_la_puede_desactivar(empresa_a, rubro_del_sistema):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="catálogo del sistema"):
            tipologias.desactivar(rubro_del_sistema.pk)


def test_cada_empresa_ve_lo_suyo_mas_lo_del_sistema(
    empresa_a, empresa_b, rubro_del_sistema, rubro_de
):
    rubro_de(empresa_a, "Farmacia")
    rubro_de(empresa_b, "Ferretería")

    with empresa(empresa_a.id):
        nombres = {t.nombre for t in tipologias.de(AGRUPADOR.RUBRO)}

    assert nombres == {"Comercio", "Farmacia"}


def test_sin_empresa_en_el_contexto_se_ven_SOLO_las_del_sistema(empresa_a, rubro_de):
    rubro_de(empresa_a, "Farmacia")

    # Sin `with empresa(...)`: solo las globales.
    nombres = {t.nombre for t in tipologias.de(AGRUPADOR.RUBRO)}

    assert nombres == {"Comercio"}


def test_no_se_puede_tocar_la_de_otra_empresa(empresa_a, empresa_b, rubro_de):
    ajena = rubro_de(empresa_b, "Ferretería")

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="No existe"):
            tipologias.actualizar(ajena.pk, nombre="Robada")


def test_el_agrupador_tiene_que_estar_declarado(empresa_a):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="agrupador 999 no existe"):
            tipologias.crear(agrupador=999, nombre="Fantasma")


def test_no_se_repite_el_nombre_en_la_misma_lista(empresa_a, rubro_de):
    rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Ya existe 'Farmacia'"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_dos_empresas_pueden_usar_el_mismo_nombre(empresa_a, empresa_b, rubro_de):
    rubro_de(empresa_a, "Farmacia")
    otra = rubro_de(empresa_b, "Farmacia")

    assert otra.pk is not None


def test_el_mismo_nombre_en_listas_distintas_no_choca(empresa_a, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)
    permitir_ampliar(empresa_a, AGRUPADOR.TIPO_EMPRESA)

    with empresa(empresa_a.id):
        tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Otro")
        fila = tipologias.crear(agrupador=AGRUPADOR.TIPO_EMPRESA, nombre="Otro")

    assert fila.pk is not None


def test_desactivar_es_soft_delete(empresa_a, rubro_de):
    propia = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        fila = tipologias.desactivar(propia.pk)

        assert fila.estado == Tipologia.Estado.INACTIVO
        # La fila sigue existiendo; solo deja de ofrecerse.
        assert tipologias.obtener(propia.pk) is not None
        assert propia.pk not in {t.pk for t in tipologias.de(AGRUPADOR.RUBRO)}


def test_no_se_puede_cambiar_de_agrupador(empresa_a, rubro_de):
    propia = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        with pytest.raises(TypeError):
            tipologias.actualizar(propia.pk, agrupador=AGRUPADOR.TIPO_EMPRESA)
