import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from comun.tipologias.management.commands.cargar_tipologias import CATALOGO
from comun.tipologias.models import Tipologia
from core.tenancy import empresa, sin_filtro_de_empresa

pytestmark = pytest.mark.django_db


@pytest.fixture
def cabecera_de_rubros(db):
    """La cabecera de la lista de rubros, tal como la carga la semilla."""
    with sin_filtro_de_empresa():
        return Tipologia.objects.create(
            empresa=None, agrupador=AGRUPADOR.RUBRO, nombre="Rubros", indice=0
        )


def test_la_cabecera_no_sale_en_el_combo(empresa_a, cabecera_de_rubros, rubro_de):
    rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        nombres = {t.nombre for t in tipologias.de(AGRUPADOR.RUBRO)}

    assert cabecera_de_rubros.nombre not in nombres
    assert nombres == {"Comercio", "Farmacia"}


def test_obtener_no_devuelve_la_cabecera(empresa_a, cabecera_de_rubros):
    with empresa(empresa_a.id):
        assert tipologias.obtener(cabecera_de_rubros.pk) is None


def test_obtener_varias_tampoco(empresa_a, cabecera_de_rubros, rubro_de):
    propia = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        encontradas = tipologias.obtener_varias(
            [cabecera_de_rubros.pk, propia.pk]
        )

    assert list(encontradas) == [propia.pk]


def test_es_del_agrupador_rechaza_la_cabecera(empresa_a, cabecera_de_rubros):
    with empresa(empresa_a.id):
        assert (
            tipologias.es_del_agrupador(cabecera_de_rubros.pk, AGRUPADOR.RUBRO)
            is False
        )


def test_la_cabecera_no_se_puede_ocultar(empresa_a, cabecera_de_rubros):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="No existe"):
            tipologias.ocultar(cabecera_de_rubros.pk)


def test_no_se_puede_crear_un_valor_con_indice_0(empresa_a, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="reservado"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia", indice=0)


def test_tampoco_se_puede_mover_un_valor_al_indice_0(empresa_a, rubro_de):
    propia = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="reservado"):
            tipologias.actualizar(propia.pk, indice=0)


def test_sin_indice_el_valor_va_al_final(empresa_a, permitir_ampliar):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_a.id):
        primera = tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")
        segunda = tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Kiosco")

    assert primera.indice >= 1
    assert segunda.indice == primera.indice + 1


def test_el_indice_sigue_la_numeracion_de_lo_heredado(
    empresa_a, sucursal_a, cabecera_de_rubros, rubro_de, permitir_ampliar
):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")
    permitir_ampliar(sucursal_a, AGRUPADOR.RUBRO)

    with empresa(sucursal_a.id):
        propia = tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Kiosco")

    assert propia.indice > de_la_matriz.indice


def test_por_graphql_tampoco_hace_falta_mandar_indice(empresa_a, permitir_ampliar):
    from config.schema import schema

    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    consulta = """
        mutation ($ag: Int!) {
          crearTipologia(datos: { agrupador: $ag, nombre: "Farmacia" }) {
            nombre indice
          }
        }
    """
    with empresa(empresa_a.id):
        resultado = schema.execute_sync(
            consulta, variable_values={"ag": int(AGRUPADOR.RUBRO)}
        )

    assert resultado.errors is None
    assert resultado.data["crearTipologia"]["indice"] >= 1


def test_un_valor_no_se_puede_llamar_como_su_lista(
    empresa_a, cabecera_de_rubros, permitir_ampliar
):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Ya existe 'Rubros'"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Rubros")


def test_la_semilla_deja_los_valores_del_1_en_adelante():
    call_command("cargar_tipologias")

    with sin_filtro_de_empresa():
        rubros = Tipologia.objects.del_agrupador(AGRUPADOR.RUBRO).order_by("indice")

    # Los índices y el nombre salen del CATÁLOGO, no escritos a mano: lo
    # que se prueba es la REGLA —cabecera en 0, valores del 1 en adelante,
    # sin huecos—, y eso no cambia porque se agregue o se saque un rubro.
    nombre_lista, valores = CATALOGO[AGRUPADOR.RUBRO]

    assert [r.indice for r in rubros] == list(range(len(valores) + 1))
    assert rubros[0].nombre == nombre_lista


def test_la_semilla_es_idempotente_con_la_cabecera():
    call_command("cargar_tipologias")
    call_command("cargar_tipologias")

    with sin_filtro_de_empresa():
        cabeceras = Tipologia.objects.cabeceras().del_agrupador(AGRUPADOR.RUBRO)

    assert cabeceras.count() == 1
