import pytest
from django.core.exceptions import ValidationError

from comun.idiomas import api as idiomas

pytestmark = pytest.mark.django_db


def test_crear_idioma(db):
    idioma = idiomas.crear_idioma(codigo="es", nombre="Español")

    assert idioma.pk is not None
    assert idioma.activo is True


def test_no_se_repite_el_codigo(espanol):
    with pytest.raises(ValidationError, match="código 'es'"):
        idiomas.crear_idioma(codigo="es", nombre="Castellano")


def test_el_codigo_se_guarda_en_minusculas(db):
    idioma = idiomas.crear_idioma(codigo="  ES-BO  ", nombre="Español de Bolivia")

    assert idioma.codigo == "es-bo"


@pytest.mark.parametrize("codigo", ["es", "en", "qu", "ay", "es-bo", "spa"])
def test_formas_validas(codigo, db):
    assert idiomas.crear_idioma(codigo=codigo, nombre="X").codigo == codigo


@pytest.mark.parametrize("codigo", ["e", "español", "ES_BO", "es-", "es-bolivia", ""])
def test_formas_invalidas(codigo, db):
    with pytest.raises(ValidationError, match="código de idioma"):
        idiomas.crear_idioma(codigo=codigo, nombre="X")


def test_un_codigo_bien_formado_pero_inexistente_pasa(db):
    assert idiomas.crear_idioma(codigo="zz", nombre="Inventado").codigo == "zz"


def test_desactivar_es_soft_delete(espanol):
    idiomas.desactivar_idioma(espanol.pk)

    idioma = idiomas.obtener_idioma(espanol.pk)
    assert idioma is not None
    assert idioma.activo is False


def test_activar_es_la_vuelta_atras(espanol):
    idiomas.desactivar_idioma(espanol.pk)
    idiomas.activar_idioma(espanol.pk)

    assert idiomas.obtener_idioma(espanol.pk).activo is True


def test_desactivar_y_activar_son_idempotentes(espanol):
    idiomas.desactivar_idioma(espanol.pk)
    idiomas.desactivar_idioma(espanol.pk)
    assert idiomas.obtener_idioma(espanol.pk).activo is False

    idiomas.activar_idioma(espanol.pk)
    idiomas.activar_idioma(espanol.pk)
    assert idiomas.obtener_idioma(espanol.pk).activo is True


def test_solo_activos_filtra(espanol, ingles):
    idiomas.desactivar_idioma(ingles.pk)

    codigos = [i.codigo for i in idiomas.listar_idiomas(solo_activos=True)]

    assert codigos == ["es"]


def test_actualizar_no_recibe_activo(espanol):
    with pytest.raises(TypeError):
        idiomas.actualizar_idioma(espanol.pk, activo=False)


def test_actualizar_no_choca_consigo_mismo(espanol):
    idioma = idiomas.actualizar_idioma(espanol.pk, nombre="Castellano")

    assert idioma.nombre == "Castellano"
    assert idioma.codigo == "es"


def test_obtener_por_codigo_no_distingue_mayusculas(espanol):
    assert idiomas.obtener_por_codigo("ES").pk == espanol.pk


def test_un_idioma_inexistente_da_error_legible(db):
    with pytest.raises(ValidationError, match="No existe el idioma"):
        idiomas.desactivar_idioma(99999)
