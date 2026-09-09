import pytest
from django.core.exceptions import ValidationError

from comun.geografia import api as geografia

pytestmark = pytest.mark.django_db


def test_crear_pais(estado_activo):
    pais = geografia.crear_pais(
        cod_pais="BO", nombre="Bolivia", codigo_iso="BOL", estado_id=estado_activo.pk
    )

    assert pais.pk is not None
    assert pais.estado_id == estado_activo.pk


def test_el_estado_tiene_que_ser_del_agrupador_correcto(tipologia_de_otro_agrupador):
    with pytest.raises(ValidationError, match="Se esperaba un estado de país"):
        geografia.crear_pais(
            cod_pais="BO",
            nombre="Bolivia",
            codigo_iso="BOL",
            estado_id=tipologia_de_otro_agrupador.pk,
        )


def test_no_se_repite_el_codigo_iso(bolivia, estado_activo):
    with pytest.raises(ValidationError, match="código ISO"):
        geografia.crear_pais(
            cod_pais="XX", nombre="Otro", codigo_iso="BOL", estado_id=estado_activo.pk
        )


def test_no_se_repite_el_cod_pais(bolivia, estado_activo):
    with pytest.raises(ValidationError, match="código 'BO'"):
        geografia.crear_pais(
            cod_pais="BO", nombre="Otro", codigo_iso="XXX", estado_id=estado_activo.pk
        )


def test_actualizar_no_choca_consigo_mismo(bolivia):
    pais = geografia.actualizar_pais(bolivia.pk, nombre="Estado Plurinacional")

    assert pais.nombre == "Estado Plurinacional"
    assert pais.codigo_iso == "BOL"


def test_actualizar_rechaza_un_estado_de_otro_agrupador(
    bolivia, tipologia_de_otro_agrupador
):
    with pytest.raises(ValidationError, match="Se esperaba un estado de país"):
        geografia.actualizar_pais(
            bolivia.pk, estado_id=tipologia_de_otro_agrupador.pk
        )


def test_desactivar_es_soft_delete(bolivia, estado_de_baja):
    pais = geografia.desactivar_pais(bolivia.pk)

    assert pais.estado_id == estado_de_baja.pk
    assert geografia.obtener_pais(bolivia.pk) is not None


def test_desactivar_avisa_si_faltan_las_semillas(bolivia):
    with pytest.raises(ValidationError, match="cargar_semillas"):
        geografia.desactivar_pais(bolivia.pk)
