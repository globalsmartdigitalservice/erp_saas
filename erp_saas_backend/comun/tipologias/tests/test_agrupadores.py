import pytest
from django.core.management import call_command

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, INDICE_CABECERA
from comun.tipologias.management.commands.cargar_tipologias import CATALOGO


def test_agrupadores_sin_duplicados():
    """En un `IntegerChoices`, dos constantes con el mismo número NO dan
    error: la segunda se vuelve un alias de la primera, en silencio."""
    valores = [miembro.value for miembro in AGRUPADOR]

    assert len(valores) == len(set(valores)), (
        "Hay agrupadores con el mismo número. El IntegerChoices los convierte "
        "en alias sin avisar y dos listas distintas quedan mezcladas."
    )


def test_los_agrupadores_arrancan_en_1():
    assert min(miembro.value for miembro in AGRUPADOR) >= 1


def test_toda_lista_declarada_tiene_nombre_en_la_semilla():
    declarados = set(AGRUPADOR.values)
    con_nombre = {int(agrupador) for agrupador in CATALOGO}

    assert declarados == con_nombre, (
        "Estas listas están declaradas y no tienen cabecera en la semilla, o "
        f"al revés: {declarados ^ con_nombre}"
    )


def test_ninguna_cabecera_repite_el_nombre_de_otra():
    nombres = [nombre for nombre, _ in CATALOGO.values()]

    assert len(nombres) == len(set(nombres))


def test_ningun_valor_se_llama_como_su_lista():
    for nombre_lista, valores in CATALOGO.values():
        nombres = [nombre for nombre, _ in valores]
        assert nombre_lista not in nombres, nombre_lista


def test_ningun_valor_se_repite_dentro_de_su_lista():
    for nombre_lista, valores in CATALOGO.values():
        nombres = [nombre for nombre, _ in valores]
        repetidos = {n for n in nombres if nombres.count(n) > 1}
        assert not repetidos, f"{nombre_lista}: {sorted(repetidos)}"


@pytest.mark.django_db
def test_la_semilla_carga_una_cabecera_por_lista():
    call_command("cargar_tipologias")

    cabeceras = tipologias.agrupadores()

    assert {c.agrupador for c in cabeceras} == set(AGRUPADOR.values)
    assert all(c.indice == INDICE_CABECERA for c in cabeceras)
    assert all(c.empresa_id is None for c in cabeceras)


@pytest.mark.django_db
def test_el_nombre_de_la_lista_sale_de_la_tabla():
    call_command("cargar_tipologias")

    assert tipologias.nombre_de_la_lista(AGRUPADOR.RUBRO) == "RUBRO O SECTOR"


@pytest.mark.django_db
def test_sin_semilla_no_hay_nombres():
    assert tipologias.agrupadores() == []
    assert tipologias.nombre_de_la_lista(AGRUPADOR.RUBRO) is None
