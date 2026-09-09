import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from comun.tipologias.models import Tipologia
from config.schema import schema
from core.tenancy import empresa

pytestmark = pytest.mark.django_db


def _nombres_que_ve(la_empresa, agrupador=AGRUPADOR.RUBRO):
    with empresa(la_empresa.id):
        return {t.nombre for t in tipologias.de(agrupador)}


def test_la_sucursal_ve_lo_de_su_matriz(empresa_a, sucursal_a, rubro_de):
    rubro_de(empresa_a, "Farmacia")

    assert "Farmacia" in _nombres_que_ve(sucursal_a)


def test_la_sucursal_tambien_ve_las_de_fabrica(sucursal_a, rubro_del_sistema):
    assert "Comercio" in _nombres_que_ve(sucursal_a)


def test_la_herencia_NO_sube(empresa_a, sucursal_a, rubro_de):
    rubro_de(sucursal_a, "Kiosco")

    assert "Kiosco" not in _nombres_que_ve(empresa_a)
    assert "Kiosco" in _nombres_que_ve(sucursal_a)


def test_otro_cliente_no_ve_nada_del_grupo(empresa_a, sucursal_a, empresa_b, rubro_de):
    rubro_de(empresa_a, "Farmacia")
    rubro_de(sucursal_a, "Kiosco")

    assert _nombres_que_ve(empresa_b) == {"Comercio"}


def test_la_sucursal_no_puede_modificar_lo_de_la_matriz(
    empresa_a, sucursal_a, rubro_de
):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")

    with empresa(sucursal_a.id):
        with pytest.raises(ValidationError, match="casa matriz"):
            tipologias.actualizar(de_la_matriz.pk, nombre="Robada")


def test_la_sucursal_no_puede_desactivar_lo_de_la_matriz(
    empresa_a, sucursal_a, rubro_de
):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")

    with empresa(sucursal_a.id):
        with pytest.raises(ValidationError, match="casa matriz"):
            tipologias.desactivar(de_la_matriz.pk)


def test_la_sucursal_si_puede_con_lo_suyo(sucursal_a, rubro_de):
    propia = rubro_de(sucursal_a, "Kiosco")

    with empresa(sucursal_a.id):
        fila = tipologias.actualizar(propia.pk, nombre="Kiosco 24h")

    assert fila.nombre == "Kiosco 24h"


def test_la_matriz_tampoco_toca_lo_de_su_sucursal(empresa_a, sucursal_a, rubro_de):
    de_la_sucursal = rubro_de(sucursal_a, "Kiosco")

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="No existe"):
            tipologias.actualizar(de_la_sucursal.pk, nombre="Robada")


def test_la_sucursal_se_oculta_un_valor_heredado(empresa_a, sucursal_a, rubro_de):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")

    with empresa(sucursal_a.id):
        tipologias.ocultar(de_la_matriz.pk)

    assert "Farmacia" not in _nombres_que_ve(sucursal_a)


def test_ocultar_no_afecta_a_nadie_mas(
    empresa_a, sucursal_a, crear_empresa, rubro_de
):
    hermana = crear_empresa("Otra sucursal de A", padre=empresa_a)
    de_la_matriz = rubro_de(empresa_a, "Farmacia")

    with empresa(sucursal_a.id):
        tipologias.ocultar(de_la_matriz.pk)

    assert "Farmacia" in _nombres_que_ve(empresa_a)
    assert "Farmacia" in _nombres_que_ve(hermana)


def test_desactivar_SI_se_lo_saca_a_todo_el_grupo(empresa_a, sucursal_a, rubro_de):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        tipologias.desactivar(de_la_matriz.pk)

    assert "Farmacia" not in _nombres_que_ve(sucursal_a)


def test_la_matriz_puede_ocultarse_un_valor_PROPIO(empresa_a, sucursal_a, rubro_de):
    propia = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        tipologias.ocultar(propia.pk)

    assert "Farmacia" not in _nombres_que_ve(empresa_a)
    assert "Farmacia" in _nombres_que_ve(sucursal_a)


def test_ocultar_es_idempotente(empresa_a, rubro_de):
    propia = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        tipologias.ocultar(propia.pk)
        tipologias.ocultar(propia.pk)

        assert tipologias.esta_oculta(propia.pk) is True
        assert len(tipologias.listar_ocultas()) == 1


def test_mostrar_deshace_el_ocultamiento(empresa_a, sucursal_a, rubro_de):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")

    with empresa(sucursal_a.id):
        tipologias.ocultar(de_la_matriz.pk)
        assert tipologias.mostrar(de_la_matriz.pk) == 1

    assert "Farmacia" in _nombres_que_ve(sucursal_a)


def test_mostrar_lo_que_no_estaba_oculto_no_falla(empresa_a, rubro_de):
    propia = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        assert tipologias.mostrar(propia.pk) == 0


def test_lo_oculto_sale_por_listar_ocultas(empresa_a, sucursal_a, rubro_de):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")

    with empresa(sucursal_a.id):
        tipologias.ocultar(de_la_matriz.pk)

        assert [t.nombre for t in tipologias.listar_ocultas()] == ["Farmacia"]
        assert tipologias.listar_ocultas(AGRUPADOR.TIPO_EMPRESA) == []


def test_no_se_puede_ocultar_lo_de_otro_cliente(empresa_a, empresa_b, rubro_de):
    ajena = rubro_de(empresa_b, "Ferretería")

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="No existe"):
            tipologias.ocultar(ajena.pk)


def test_ocultar_sin_empresa_en_el_contexto_falla(db, catalogo):
    with pytest.raises(ValidationError, match="No hay empresa en el contexto"):
        tipologias.ocultar(catalogo["rubro"].pk)


def test_la_sucursal_no_repite_un_nombre_de_la_matriz(
    empresa_a, sucursal_a, rubro_de, permitir_ampliar
):
    rubro_de(empresa_a, "Farmacia")
    permitir_ampliar(sucursal_a, AGRUPADOR.RUBRO)

    with empresa(sucursal_a.id):
        with pytest.raises(ValidationError, match="Ya existe 'Farmacia'"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_tampoco_repite_un_nombre_de_fabrica(
    sucursal_a, rubro_del_sistema, permitir_ampliar
):
    permitir_ampliar(sucursal_a, AGRUPADOR.RUBRO)

    with empresa(sucursal_a.id):
        with pytest.raises(ValidationError, match="Ya existe 'Comercio'"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Comercio")


def test_si_lo_oculto_entonces_SI_puede_usar_ese_nombre(
    empresa_a, sucursal_a, rubro_de, permitir_ampliar
):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")
    permitir_ampliar(sucursal_a, AGRUPADOR.RUBRO)

    with empresa(sucursal_a.id):
        tipologias.ocultar(de_la_matriz.pk)
        propia = tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")

    assert propia.empresa_id == sucursal_a.id
    assert _nombres_que_ve(sucursal_a) == {"Comercio", "Farmacia"}


def test_una_fila_desactivada_sigue_ocupando_el_nombre(
    empresa_a, rubro_de, permitir_ampliar
):
    propia = rubro_de(empresa_a, "Farmacia")

    with empresa(empresa_a.id):
        tipologias.desactivar(propia.pk)

        with pytest.raises(ValidationError, match="Ya existe 'Farmacia'"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_el_permiso_de_la_matriz_habilita_a_la_sucursal(
    empresa_a, sucursal_a, permitir_ampliar
):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(sucursal_a.id):
        fila = tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Kiosco")

    assert fila.empresa_id == sucursal_a.id


def test_el_permiso_sigue_sin_cruzar_a_otro_cliente(
    empresa_a, empresa_b, permitir_ampliar
):
    permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)

    with empresa(empresa_b.id):
        with pytest.raises(ValidationError, match="no puede agregar valores propios"):
            tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre="Farmacia")


def test_el_schema_dice_cual_es_editable(empresa_a, sucursal_a, rubro_de):
    rubro_de(empresa_a, "Farmacia")
    rubro_de(sucursal_a, "Kiosco")

    with empresa(sucursal_a.id):
        resultado = schema.execute_sync(
            "query ($ag: Int!) { tipologias(agrupador: $ag) "
            "{ nombre esDelSistema esPropia } }",
            variable_values={"ag": int(AGRUPADOR.RUBRO)},
        )

    assert resultado.errors is None
    assert resultado.data["tipologias"] == [
        {"nombre": "Comercio", "esDelSistema": True, "esPropia": False},
        {"nombre": "Farmacia", "esDelSistema": False, "esPropia": False},
        {"nombre": "Kiosco", "esDelSistema": False, "esPropia": True},
    ]


def test_las_mutations_de_ocultar_y_mostrar(empresa_a, sucursal_a, rubro_de):
    de_la_matriz = rubro_de(empresa_a, "Farmacia")

    with empresa(sucursal_a.id):
        ocultar = schema.execute_sync(
            "mutation ($id: ID!) { ocultarTipologia(id: $id) }",
            variable_values={"id": str(de_la_matriz.pk)},
        )
        assert ocultar.errors is None
        assert ocultar.data["ocultarTipologia"] is True

        ocultas = schema.execute_sync("{ tipologiasOcultas { nombre } }")
        assert ocultas.data["tipologiasOcultas"] == [{"nombre": "Farmacia"}]

        mostrar = schema.execute_sync(
            "mutation ($id: ID!) { mostrarTipologia(id: $id) }",
            variable_values={"id": str(de_la_matriz.pk)},
        )
        assert mostrar.data["mostrarTipologia"] is True

    assert "Farmacia" in _nombres_que_ve(sucursal_a)


def test_el_ambito_no_agrega_consultas_por_valor(empresa_a, sucursal_a, rubro_de):
    rubro_de(empresa_a, "Farmacia")

    with empresa(sucursal_a.id):
        with CaptureQueriesContext(connection) as con_uno:
            tipologias.de(AGRUPADOR.RUBRO)

    for nombre in ("Ferretería", "Kiosco", "Panadería"):
        rubro_de(empresa_a, nombre)

    with empresa(sucursal_a.id):
        with CaptureQueriesContext(connection) as con_cuatro:
            assert len(tipologias.de(AGRUPADOR.RUBRO)) == 5  # 4 + "Comercio"

    assert len(con_cuatro) == len(con_uno)
