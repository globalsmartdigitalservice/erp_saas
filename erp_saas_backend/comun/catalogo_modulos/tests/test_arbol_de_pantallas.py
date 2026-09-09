import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from comun.catalogo_modulos import api as modulos

pytestmark = pytest.mark.django_db


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def ventas(activo):
    return modulos.crear(codigo="VENTAS", nombre="Ventas", estado_id=activo.id)


@pytest.fixture
def facturas(ventas, activo):
    return modulos.crear_sub_modulo(
        codigo="VENTAS_FACTURAS",
        modulo_sistema_id=ventas.id,
        nombre="Facturas",
        ruta="/ventas/facturas",
        estado_id=activo.id,
    )


@pytest.fixture
def permisos(db):
    """Permisos de Django de mentira, para colgarles funcionalidades."""
    tipo = ContentType.objects.get_for_model(Permission)

    def _permiso(codename):
        return Permission.objects.create(
            codename=codename, name=codename.replace("_", " "), content_type=tipo
        )

    return _permiso


def test_crear_una_pantalla(facturas, ventas):
    assert facturas.codigo == "VENTAS_FACTURAS"
    assert facturas.modulo_sistema_id == ventas.id
    assert facturas.ruta == "/ventas/facturas"


def test_la_ruta_se_normaliza(ventas, activo):
    pantalla = modulos.crear_sub_modulo(
        codigo="VENTAS_NOTAS",
        modulo_sistema_id=ventas.id,
        nombre="Notas de crédito",
        ruta="  /Ventas/Notas/  ",
        estado_id=activo.id,
    )

    assert pantalla.ruta == "/ventas/notas"


def test_no_se_repite_la_ruta(facturas, ventas, activo):
    with pytest.raises(ValidationError, match="misma dirección"):
        modulos.crear_sub_modulo(
            codigo="OTRO_CODIGO",
            modulo_sistema_id=ventas.id,
            nombre="Otra pantalla",
            ruta="/VENTAS/FACTURAS",
            estado_id=activo.id,
        )


def test_la_ruta_no_puede_ir_vacia(ventas, activo):
    with pytest.raises(ValidationError, match="no puede ir vacía"):
        modulos.crear_sub_modulo(
            codigo="SIN_RUTA",
            modulo_sistema_id=ventas.id,
            nombre="Sin ruta",
            ruta="   ",
            estado_id=activo.id,
        )


def test_la_ruta_tiene_que_empezar_con_barra(ventas, activo):
    with pytest.raises(ValidationError, match="empezar con"):
        modulos.crear_sub_modulo(
            codigo="MALA_RUTA",
            modulo_sistema_id=ventas.id,
            nombre="Mala",
            ruta="ventas/facturas",
            estado_id=activo.id,
        )


def test_el_codigo_se_guarda_en_mayusculas(ventas, activo):
    pantalla = modulos.crear_sub_modulo(
        codigo="  ventas_pedidos  ",
        modulo_sistema_id=ventas.id,
        nombre="Pedidos",
        ruta="/ventas/pedidos",
        estado_id=activo.id,
    )

    assert pantalla.codigo == "VENTAS_PEDIDOS"


def test_no_se_repite_el_nombre_dentro_del_modulo(facturas, ventas, activo):
    with pytest.raises(ValidationError, match="ya tiene un submódulo"):
        modulos.crear_sub_modulo(
            codigo="OTRA",
            modulo_sistema_id=ventas.id,
            nombre="Facturas",
            ruta="/ventas/otra",
            estado_id=activo.id,
        )


def test_el_mismo_nombre_si_se_repite_entre_modulos(facturas, activo):
    compras = modulos.crear(codigo="COMPRAS", nombre="Compras", estado_id=activo.id)

    otra = modulos.crear_sub_modulo(
        codigo="COMPRAS_FACTURAS",
        modulo_sistema_id=compras.id,
        nombre="Facturas",
        ruta="/compras/facturas",
        estado_id=activo.id,
    )

    assert otra.nombre == facturas.nombre


def test_no_se_cuelga_de_un_modulo_que_no_existe(activo):
    with pytest.raises(ValidationError, match="No existe el módulo"):
        modulos.crear_sub_modulo(
            codigo="X",
            modulo_sistema_id=999999,
            nombre="X",
            ruta="/x",
            estado_id=activo.id,
        )


def test_el_estado_tiene_que_ser_del_agrupador_correcto(ventas, catalogo):
    with pytest.raises(ValidationError, match="Se esperaba un estado del registro"):
        modulos.crear_sub_modulo(
            codigo="X",
            modulo_sistema_id=ventas.id,
            nombre="X",
            ruta="/x",
            estado_id=catalogo["rubro"].id,
        )


def test_tres_acciones_en_la_misma_pantalla(facturas, permisos, activo):
    for nombre, codename in [
        ("Emitir factura", "emitir_factura"),
        ("Anular factura", "anular_factura"),
        ("Ver factura", "ver_factura"),
    ]:
        modulos.crear_funcionalidad(
            sub_modulo_id=facturas.id,
            auth_permission_id=permisos(codename).id,
            nombre=nombre,
            estado_id=activo.id,
        )

    acciones = modulos.listar_funcionalidades_de(facturas.id)

    assert len(acciones) == 3
    assert {a.sub_modulo.ruta for a in acciones} == {"/ventas/facturas"}


def test_un_permiso_no_puede_estar_en_dos_funcionalidades(
    facturas, permisos, activo
):
    permiso = permisos("anular_factura")
    modulos.crear_funcionalidad(
        sub_modulo_id=facturas.id,
        auth_permission_id=permiso.id,
        nombre="Anular factura",
        estado_id=activo.id,
    )

    with pytest.raises(ValidationError, match="ya está descrito"):
        modulos.crear_funcionalidad(
            sub_modulo_id=facturas.id,
            auth_permission_id=permiso.id,
            nombre="Anular (otra vez)",
            estado_id=activo.id,
        )


def test_no_se_cuelga_de_un_permiso_que_no_existe(facturas, activo):
    with pytest.raises(ValidationError, match="No existe el permiso"):
        modulos.crear_funcionalidad(
            sub_modulo_id=facturas.id,
            auth_permission_id=999999,
            nombre="X",
            estado_id=activo.id,
        )


def test_no_se_repite_el_nombre_dentro_de_la_pantalla(facturas, permisos, activo):
    modulos.crear_funcionalidad(
        sub_modulo_id=facturas.id,
        auth_permission_id=permisos("emitir_factura").id,
        nombre="Emitir factura",
        estado_id=activo.id,
    )

    with pytest.raises(ValidationError, match="ya tiene una funcionalidad"):
        modulos.crear_funcionalidad(
            sub_modulo_id=facturas.id,
            auth_permission_id=permisos("emitir_factura_2").id,
            nombre="Emitir factura",
            estado_id=activo.id,
        )


def test_desde_el_permiso_se_llega_a_su_funcionalidad(facturas, permisos, activo):
    permiso = permisos("ver_factura")
    creada = modulos.crear_funcionalidad(
        sub_modulo_id=facturas.id,
        auth_permission_id=permiso.id,
        nombre="Ver factura",
        estado_id=activo.id,
    )

    assert modulos.funcionalidad_del_permiso(permiso.id).id == creada.id


def test_no_se_da_de_baja_una_pantalla_con_acciones(facturas, permisos, activo, catalogo):
    from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA

    catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)
    modulos.crear_funcionalidad(
        sub_modulo_id=facturas.id,
        auth_permission_id=permisos("anular_factura").id,
        nombre="Anular factura",
        estado_id=activo.id,
    )

    with pytest.raises(ValidationError, match="todavía tiene"):
        modulos.desactivar_sub_modulo(facturas.id)


def test_la_pantalla_sin_acciones_si_se_da_de_baja(facturas, catalogo):
    from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA

    baja = catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)

    assert modulos.desactivar_sub_modulo(facturas.id).estado_id == baja.id


def test_listar_pantallas_no_crece_con_la_cantidad(ventas, activo, django_assert_num_queries):
    for i in range(20):
        modulos.crear_sub_modulo(
            codigo=f"VENTAS_P{i}",
            modulo_sistema_id=ventas.id,
            nombre=f"Pantalla {i}",
            ruta=f"/ventas/p{i}",
            estado_id=activo.id,
        )

    with django_assert_num_queries(1):
        pantallas = modulos.listar_sub_modulos()
        # Tocar la relación es lo que dispararía el N+1 si faltara.
        [p.modulo_sistema.codigo for p in pantallas]


def test_listar_acciones_no_crece_con_la_cantidad(
    facturas, permisos, activo, django_assert_num_queries
):
    for i in range(20):
        modulos.crear_funcionalidad(
            sub_modulo_id=facturas.id,
            auth_permission_id=permisos(f"accion_{i}").id,
            nombre=f"Acción {i}",
            estado_id=activo.id,
        )

    with django_assert_num_queries(1):
        acciones = modulos.listar_funcionalidades()
        [(a.sub_modulo.ruta, a.auth_permission.codename) for a in acciones]


def test_el_menu_de_varios_modulos_es_una_sola_consulta(
    activo, django_assert_num_queries
):
    ids = []
    for i in range(5):
        modulo = modulos.crear(
            codigo=f"MOD{i}", nombre=f"Módulo {i}", estado_id=activo.id
        )
        ids.append(modulo.id)
        modulos.crear_sub_modulo(
            codigo=f"MOD{i}_INICIO",
            modulo_sistema_id=modulo.id,
            nombre="Inicio",
            ruta=f"/mod{i}/inicio",
            estado_id=activo.id,
        )

    with django_assert_num_queries(1):
        pantallas = modulos.listar_sub_modulos_de_varios(ids)
        [p.modulo_sistema.codigo for p in pantallas]

    assert len(pantallas) == 5
