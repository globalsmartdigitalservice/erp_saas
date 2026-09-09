import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext

from comun.idiomas import api as idiomas
from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa, sin_filtro_de_empresa

pytestmark = pytest.mark.django_db

TABLA = "conf_tipologia"


@pytest.fixture
def rubro_del_sistema(catalogo):
    """
    Un valor de fábrica: lo ven todas las empresas.

    `ingles` no se declara acá: ya está en el conftest de la app.
    """
    return catalogo["tipologia"](AGRUPADOR.RUBRO, "Construcción")


def _de_fabrica(entidad_id, idioma_id, texto, campo="nombre"):
    """Carga una traducción del catálogo del sistema, como la semilla."""
    with sin_filtro_de_empresa():
        return idiomas.guardar_traduccion_de_fabrica(
            entidad_tipo=TABLA,
            entidad_id=entidad_id,
            campo=campo,
            idioma_id=idioma_id,
            texto=texto,
        )


def test_guardar_y_leer_una_traduccion(empresa_a, rubro_del_sistema, ingles):
    with empresa(empresa_a.pk):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )

        textos = idiomas.traducciones_de(
            TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
        )

    assert textos == {rubro_del_sistema.pk: "Construction"}


def test_lo_que_no_tiene_traduccion_no_aparece(empresa_a, rubro_del_sistema, ingles):
    with empresa(empresa_a.pk):
        textos = idiomas.traducciones_de(
            TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
        )

    assert textos == {}
    assert textos.get(rubro_del_sistema.pk, rubro_del_sistema.nombre) == "Construcción"


def test_guardar_dos_veces_actualiza_y_no_duplica(
    empresa_a, rubro_del_sistema, ingles
):
    with empresa(empresa_a.pk):
        primera = idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Constructions",
        )
        segunda = idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )

        filas = idiomas.listar_traducciones_de(TABLA, rubro_del_sistema.pk)

    assert primera.pk == segunda.pk
    assert len(filas) == 1
    assert filas[0].texto == "Construction"


def test_el_lote_no_crece_con_la_cantidad(catalogo, empresa_a, ingles):
    rubros = [
        catalogo["tipologia"](AGRUPADOR.RUBRO, f"Rubro {i}") for i in range(5)
    ]

    with empresa(empresa_a.pk):
        for i, rubro in enumerate(rubros):
            idiomas.guardar_traduccion(
                entidad_tipo=TABLA,
                entidad_id=rubro.pk,
                campo="nombre",
                idioma_id=ingles.pk,
                texto=f"Sector {i}",
            )

        with CaptureQueriesContext(connection) as una:
            idiomas.traducciones_de(TABLA, [rubros[0].pk], "nombre", ingles.pk)

        with CaptureQueriesContext(connection) as cinco:
            idiomas.traducciones_de(
                TABLA, [r.pk for r in rubros], "nombre", ingles.pk
            )

    assert len(una) == len(cinco)


def test_el_lote_vacio_no_consulta(empresa_a, ingles):
    with empresa(empresa_a.pk), CaptureQueriesContext(connection) as consultas:
        assert idiomas.traducciones_de(TABLA, [], "nombre", ingles.pk) == {}

    assert len(consultas) == 0


def test_una_tabla_desconocida_se_rechaza(empresa_a, rubro_del_sistema, ingles):
    with empresa(empresa_a.pk):
        with pytest.raises(ValidationError, match="no está declarada como traducible"):
            idiomas.guardar_traduccion(
                entidad_tipo="conf_tipologa",
                entidad_id=rubro_del_sistema.pk,
                campo="nombre",
                idioma_id=ingles.pk,
                texto="Construction",
            )


def test_un_campo_no_declarado_se_rechaza(empresa_a, rubro_del_sistema, ingles):
    with empresa(empresa_a.pk):
        with pytest.raises(ValidationError, match="no es traducible"):
            idiomas.guardar_traduccion(
                entidad_tipo=TABLA,
                entidad_id=rubro_del_sistema.pk,
                campo="estado",
                idioma_id=ingles.pk,
                texto="Active",
            )


def test_una_fila_inexistente_se_rechaza(empresa_a, ingles):
    with empresa(empresa_a.pk):
        with pytest.raises(ValidationError, match="No existe el registro"):
            idiomas.guardar_traduccion(
                entidad_tipo=TABLA,
                entidad_id=999999,
                campo="nombre",
                idioma_id=ingles.pk,
                texto="Nada",
            )


@pytest.mark.parametrize("texto", ["", "   ", None])
def test_el_texto_vacio_se_rechaza(empresa_a, rubro_del_sistema, ingles, texto):
    with empresa(empresa_a.pk):
        with pytest.raises(ValidationError, match="no puede estar vacía"):
            idiomas.guardar_traduccion(
                entidad_tipo=TABLA,
                entidad_id=rubro_del_sistema.pk,
                campo="nombre",
                idioma_id=ingles.pk,
                texto=texto,
            )


def test_no_se_traduce_a_un_idioma_apagado(empresa_a, rubro_del_sistema, ingles):
    idiomas.desactivar_idioma(ingles.pk)

    with empresa(empresa_a.pk):
        with pytest.raises(ValidationError, match="desactivado"):
            idiomas.guardar_traduccion(
                entidad_tipo=TABLA,
                entidad_id=rubro_del_sistema.pk,
                campo="nombre",
                idioma_id=ingles.pk,
                texto="Construction",
            )


def test_sin_empresa_en_el_contexto_no_se_guarda(rubro_del_sistema, ingles):
    with pytest.raises(ValidationError, match="No hay empresa activa"):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )


def test_la_de_fabrica_exige_decir_que_cruza_empresas(rubro_del_sistema, ingles):
    with pytest.raises(ValidationError, match="sin_filtro_de_empresa"):
        idiomas.guardar_traduccion_de_fabrica(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )


def test_la_traduccion_de_otra_empresa_no_se_ve(
    empresa_a, empresa_b, rubro_del_sistema, ingles
):
    with empresa(empresa_b.pk):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Lo de B",
        )

    with empresa(empresa_a.pk):
        textos = idiomas.traducciones_de(
            TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
        )

    assert textos == {}


def test_no_se_traduce_una_fila_de_otra_empresa(catalogo, empresa_a, empresa_b, ingles):
    rubro_de_b = catalogo["tipologia"](AGRUPADOR.RUBRO, "Solo de B", empresa=empresa_b)

    with empresa(empresa_a.pk):
        with pytest.raises(ValidationError) as error:
            idiomas.guardar_traduccion(
                entidad_tipo=TABLA,
                entidad_id=rubro_de_b.pk,
                campo="nombre",
                idioma_id=ingles.pk,
                texto="Only B",
            )

    # El mensaje dice "no existe", NUNCA "no es tuya": enterarse de que
    # el id existe en otra empresa ya es una filtración.
    mensaje = "; ".join(error.value.messages)
    assert "No existe el registro" in mensaje
    assert "tuy" not in mensaje.lower()
    assert "otra empresa" not in mensaje.lower()


def test_la_de_fabrica_se_ve_desde_cualquier_empresa(
    empresa_a, empresa_b, rubro_del_sistema, ingles
):
    _de_fabrica(rubro_del_sistema.pk, ingles.pk, "Construction")

    for una in (empresa_a, empresa_b):
        with empresa(una.pk):
            textos = idiomas.traducciones_de(
                TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
            )
        assert textos == {rubro_del_sistema.pk: "Construction"}


def test_la_sucursal_hereda_la_traduccion_de_la_matriz(
    empresa_a, sucursal_a, rubro_del_sistema, ingles
):
    with empresa(empresa_a.pk):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )

    with empresa(sucursal_a.pk):
        textos = idiomas.traducciones_de(
            TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
        )

    assert textos == {rubro_del_sistema.pk: "Construction"}


def test_la_propia_le_gana_a_la_de_fabrica(empresa_a, rubro_del_sistema, ingles):
    _de_fabrica(rubro_del_sistema.pk, ingles.pk, "Construction")

    with empresa(empresa_a.pk):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Building",
        )
        textos = idiomas.traducciones_de(
            TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
        )

    assert textos == {rubro_del_sistema.pk: "Building"}


def test_guardar_lo_propio_no_pisa_lo_de_fabrica(
    empresa_a, empresa_b, rubro_del_sistema, ingles
):
    _de_fabrica(rubro_del_sistema.pk, ingles.pk, "Construction")

    with empresa(empresa_a.pk):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Building",
        )

    with empresa(empresa_b.pk):
        textos = idiomas.traducciones_de(
            TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
        )

    assert textos == {rubro_del_sistema.pk: "Construction"}


def test_la_de_la_sucursal_le_gana_a_la_de_la_matriz(
    empresa_a, sucursal_a, rubro_del_sistema, ingles
):
    with empresa(empresa_a.pk):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )

    with empresa(sucursal_a.pk):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Civil works",
        )
        textos = idiomas.traducciones_de(
            TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
        )

    assert textos == {rubro_del_sistema.pk: "Civil works"}


def test_se_borra_la_propia(empresa_a, rubro_del_sistema, ingles):
    with empresa(empresa_a.pk):
        fila = idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )

        idiomas.borrar_traduccion(fila.pk)

        assert idiomas.traducciones_de(
            TABLA, [rubro_del_sistema.pk], "nombre", ingles.pk
        ) == {}


def test_no_se_borra_la_de_fabrica(empresa_a, rubro_del_sistema, ingles):
    fila = _de_fabrica(rubro_del_sistema.pk, ingles.pk, "Construction")

    with empresa(empresa_a.pk):
        with pytest.raises(ValidationError, match="catálogo del sistema"):
            idiomas.borrar_traduccion(fila.pk)


def test_la_sucursal_no_borra_la_de_su_matriz(
    empresa_a, sucursal_a, rubro_del_sistema, ingles
):
    with empresa(empresa_a.pk):
        fila = idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )

    with empresa(sucursal_a.pk):
        with pytest.raises(ValidationError, match="casa matriz"):
            idiomas.borrar_traduccion(fila.pk)


def test_no_hay_dos_traducciones_del_mismo_campo_en_la_misma_empresa(
    empresa_a, rubro_del_sistema, ingles
):
    from comun.idiomas.models import Traduccion

    with empresa(empresa_a.pk):
        idiomas.guardar_traduccion(
            entidad_tipo=TABLA,
            entidad_id=rubro_del_sistema.pk,
            campo="nombre",
            idioma_id=ingles.pk,
            texto="Construction",
        )

    # A mano, salteando el service: la que tiene que frenar es la base.
    with pytest.raises(IntegrityError):
        with transaction.atomic(), sin_filtro_de_empresa():
            Traduccion.objects.create(
                empresa_id=empresa_a.pk,
                entidad_tipo=TABLA,
                entidad_id=rubro_del_sistema.pk,
                campo="nombre",
                idioma_id=ingles.pk,
                texto="Building",
            )


def test_no_hay_dos_traducciones_de_fabrica_iguales(rubro_del_sistema, ingles):
    from comun.idiomas.models import Traduccion

    _de_fabrica(rubro_del_sistema.pk, ingles.pk, "Construction")

    with pytest.raises(IntegrityError):
        with transaction.atomic(), sin_filtro_de_empresa():
            Traduccion.objects.create(
                empresa=None,
                entidad_tipo=TABLA,
                entidad_id=rubro_del_sistema.pk,
                campo="nombre",
                idioma_id=ingles.pk,
                texto="Building",
            )


def test_el_registro_de_traducibles_nombra_tablas_que_existen():
    """Un nombre de tabla mal escrito en el registro deja el campo
    "traducible" contra nada, y no lo avisa nadie."""
    from django.apps import apps

    from comun.idiomas import traducibles

    reales = {m._meta.db_table for m in apps.get_models()}
    declaradas = set(traducibles.TRADUCIBLES)

    assert declaradas <= reales, (
        f"El registro de traducibles nombra tablas que no existen: "
        f"{sorted(declaradas - reales)}"
    )


def test_los_campos_declarados_existen_en_su_tabla():
    from django.apps import apps

    from comun.idiomas import traducibles

    por_tabla = {m._meta.db_table: m for m in apps.get_models()}

    for tabla, campos in traducibles.TRADUCIBLES.items():
        modelo = por_tabla[tabla]
        reales = {f.name for f in modelo._meta.get_fields()}
        faltan = set(campos) - reales
        assert not faltan, f"'{tabla}' no tiene los campos {sorted(faltan)}"
