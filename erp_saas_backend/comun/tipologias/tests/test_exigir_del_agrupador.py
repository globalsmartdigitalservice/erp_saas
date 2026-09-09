import pytest
from django.core.exceptions import ValidationError

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, INDICE_CABECERA
from comun.tipologias.models import Tipologia
from core.tenancy import empresa, sin_filtro_de_empresa

pytestmark = pytest.mark.django_db


@pytest.fixture
def cabecera_de_estados(catalogo):
    """La fila `indice = 0`: el NOMBRE de la lista, no un valor."""
    with sin_filtro_de_empresa():
        return Tipologia.objects.create(
            empresa=None,
            agrupador=AGRUPADOR.ESTADO_REGISTRO,
            nombre="ESTADOS GENERALES",
            indice=INDICE_CABECERA,
        )


def test_la_cabecera_dice_que_es_una_cabecera(cabecera_de_estados):
    with pytest.raises(ValidationError) as error:
        tipologias.exigir_del_agrupador(
            cabecera_de_estados.id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
        )

    mensaje = error.value.messages[0]
    assert "NOMBRE de la lista" in mensaje
    assert "ESTADOS GENERALES" in mensaje
    # Y dice qué hacer, no solo qué está mal.
    assert "Elegí un valor" in mensaje


def test_una_tipologia_de_otra_lista_dice_cual_es(catalogo):
    with pytest.raises(ValidationError) as error:
        tipologias.exigir_del_agrupador(
            catalogo["rubro"].id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
        )

    mensaje = error.value.messages[0]
    assert catalogo["rubro"].nombre in mensaje
    assert "Se esperaba un estado del registro" in mensaje


def test_una_tipologia_que_no_existe_lo_dice(db):
    with pytest.raises(ValidationError, match="No existe la tipología 999999"):
        tipologias.exigir_del_agrupador(
            999999, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
        )


def test_la_correcta_pasa_y_devuelve_la_fila(catalogo):
    fila = tipologias.exigir_del_agrupador(
        catalogo["estado_activo"].id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )

    assert fila.id == catalogo["estado_activo"].id


def test_no_dice_el_nombre_de_una_tipologia_de_otra_empresa(
    catalogo, empresa_a, empresa_b
):
    ajena = catalogo["tipologia"](
        AGRUPADOR.RUBRO, "RUBRO SECRETO DE B", empresa=empresa_b
    )

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError) as error:
            tipologias.exigir_del_agrupador(
                ajena.id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
            )

    mensaje = error.value.messages[0]
    assert "No existe la tipología" in mensaje
    assert "SECRETO" not in mensaje
