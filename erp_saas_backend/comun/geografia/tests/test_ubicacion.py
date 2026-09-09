import pytest
from django.core.exceptions import ValidationError

from comun.geografia import api as geografia

pytestmark = pytest.mark.django_db


@pytest.fixture
def santa_cruz(bolivia, estado_activo):
    return geografia.crear_ubicacion(
        pais_id=bolivia.pk,
        nombre="Santa Cruz",
        tipo="Departamento",
        estado_id=estado_activo.pk,
    )


@pytest.fixture
def andres_ibanez(bolivia, santa_cruz, estado_activo):
    return geografia.crear_ubicacion(
        pais_id=bolivia.pk,
        nombre="Andrés Ibáñez",
        tipo="Provincia",
        estado_id=estado_activo.pk,
        division_superior_id=santa_cruz.pk,
    )


def test_una_raiz_queda_en_nivel_1(santa_cruz):
    assert santa_cruz.nivel == 1
    assert santa_cruz.division_superior_id is None


def test_el_nivel_se_calcula_desde_el_padre(andres_ibanez):
    assert andres_ibanez.nivel == 2


def test_tres_niveles(bolivia, andres_ibanez, estado_activo):
    municipio = geografia.crear_ubicacion(
        pais_id=bolivia.pk,
        nombre="Santa Cruz de la Sierra",
        tipo="Municipio",
        estado_id=estado_activo.pk,
        division_superior_id=andres_ibanez.pk,
    )

    assert municipio.nivel == 3


def test_no_puede_colgar_de_una_division_de_otro_pais(
    argentina, santa_cruz, estado_activo
):
    with pytest.raises(ValidationError, match="otro país"):
        geografia.crear_ubicacion(
            pais_id=argentina.pk,
            nombre="Córdoba",
            tipo="Provincia",
            estado_id=estado_activo.pk,
            division_superior_id=santa_cruz.pk,
        )


def test_el_estado_tiene_que_ser_del_agrupador_correcto(
    bolivia, tipologia_de_otro_agrupador
):
    with pytest.raises(ValidationError, match="Se esperaba un estado de ubicación"):
        geografia.crear_ubicacion(
            pais_id=bolivia.pk,
            nombre="Santa Cruz",
            tipo="Departamento",
            estado_id=tipologia_de_otro_agrupador.pk,
        )


def test_no_puede_colgar_de_si_misma(santa_cruz):
    with pytest.raises(ValidationError, match="de sí misma"):
        geografia.mover_ubicacion(santa_cruz.pk, santa_cruz.pk)


def test_no_puede_colgar_de_una_descendiente(santa_cruz, andres_ibanez):
    with pytest.raises(ValidationError, match="ciclo"):
        geografia.mover_ubicacion(santa_cruz.pk, andres_ibanez.pk)


def test_mover_recalcula_el_nivel(bolivia, santa_cruz, andres_ibanez, estado_activo):
    otro_depto = geografia.crear_ubicacion(
        pais_id=bolivia.pk,
        nombre="Cochabamba",
        tipo="Departamento",
        estado_id=estado_activo.pk,
    )

    movida = geografia.mover_ubicacion(andres_ibanez.pk, otro_depto.pk)

    assert movida.division_superior_id == otro_depto.pk
    assert movida.nivel == 2


def test_mover_a_raiz(andres_ibanez):
    movida = geografia.mover_ubicacion(andres_ibanez.pk, None)

    assert movida.division_superior_id is None
    assert movida.nivel == 1


def test_hijos_directos(santa_cruz, andres_ibanez):
    hijos = geografia.hijos_de(santa_cruz.pk)

    assert [h.pk for h in hijos] == [andres_ibanez.pk]


def test_desactivar_es_soft_delete(santa_cruz, estado_de_baja):
    ubicacion = geografia.desactivar_ubicacion(santa_cruz.pk)

    assert ubicacion.estado_id == estado_de_baja.pk
    assert geografia.obtener_ubicacion(santa_cruz.pk) is not None
