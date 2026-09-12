from io import StringIO

import pytest
from django.contrib.auth.models import Permission
from django.core.management import call_command

from comun.catalogo_modulos import api as modulos
from dominios.seguridad import api as seguridad
from dominios.seguridad.permisos import (
    auto_permisos,
    codename_de,
    content_type_del_ancla,
    escanear,
)
from core.tenancy import empresa

pytestmark = pytest.mark.django_db


# ── clases de mentira, como las que escribirían los otros devs ──


@auto_permisos(recurso="VENTAS_FACTURAS")
class MutationDeVentas:
    def emitir_factura(self):
        pass

    def anular_factura(self):
        pass

    def _privado(self):
        pass

    @auto_permisos(recurso="VENTAS_FACTURAS", operacion="ver_costo")
    def precio_de_costo(self):
        pass


class MutationSinDecorar:
    def hacer_algo(self):
        pass


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def pantalla_roles(activo):
    """
    La pantalla real de `SeguridadMutations`, que está decorada con
    `@auto_permisos(recurso="SEGU_ROLES")`.

    Los tests del comando van contra las mutations DE VERDAD y no contra
    clases de mentira: lo que hay que comprobar es que el escáner las
    encuentre donde realmente viven (`<app>/graphql/mutations.py`), que es
    justo lo que una clase de prueba no probaría.
    """
    seguridad_mod = modulos.crear(
        codigo="SEGURIDAD", nombre="Seguridad", estado_id=activo.id
    )
    return modulos.crear_sub_modulo(
        codigo="SEGU_ROLES",
        modulo_sistema_id=seguridad_mod.id,
        nombre="Roles",
        ruta="/seguridad/roles",
        estado_id=activo.id,
    )


def test_escanea_los_metodos_publicos_de_la_clase(db):
    codenames = {d["codename"] for d in escanear([MutationDeVentas])}

    assert "ventas_facturas_emitir_factura" in codenames
    assert "ventas_facturas_anular_factura" in codenames


def test_no_escanea_los_metodos_privados(db):
    codenames = {d["codename"] for d in escanear([MutationDeVentas])}

    assert not any("privado" in c for c in codenames)


def test_el_decorador_del_metodo_gana_sobre_el_de_la_clase(db):
    codenames = {d["codename"] for d in escanear([MutationDeVentas])}

    assert "ventas_facturas_ver_costo" in codenames
    assert "ventas_facturas_precio_de_costo" not in codenames


def test_una_clase_sin_decorar_no_declara_nada(db):
    assert escanear([MutationSinDecorar]) == []


def test_el_recurso_va_en_el_codename(db):
    assert codename_de("VENTAS_FACTURAS", "anular") == "ventas_facturas_anular"
    assert codename_de("COMPRAS_FACTURAS", "anular") == "compras_facturas_anular"


def test_el_recurso_es_obligatorio(db):
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured):
        auto_permisos(recurso="  ")


def _correr(**opciones) -> str:
    salida = StringIO()
    call_command("generar_permisos", stdout=salida, **opciones)
    return salida.getvalue()


def test_el_simulacro_no_escribe_nada(db, pantalla_roles):
    antes = Permission.objects.count()

    salida = _correr(dry_run=True)

    assert Permission.objects.count() == antes
    assert "SIMULACRO" in salida


def test_correrlo_dos_veces_no_duplica(db, pantalla_roles):
    _correr()
    despues_de_una = Permission.objects.filter(
        content_type=content_type_del_ancla()
    ).count()

    _correr()

    assert (
        Permission.objects.filter(content_type=content_type_del_ancla()).count()
        == despues_de_una
    )


def test_no_borra_los_permisos_que_ya_no_estan_en_el_codigo(db, pantalla_roles):
    """Borrar un `auth_permission` le saca capacidades EN SILENCIO a todos
    los roles que lo tenían."""
    viejo = Permission.objects.create(
        content_type=content_type_del_ancla(),
        codename="segu_roles_operacion_que_ya_no_existe",
        name="Vieja",
    )

    salida = _correr()

    assert Permission.objects.filter(pk=viejo.pk).exists()
    assert "NO se borran" in salida
    assert viejo.codename in salida


def test_avisa_cuando_un_permiso_esta_en_uso(db, pantalla_roles, activo, empresa_a):
    viejo = Permission.objects.create(
        content_type=content_type_del_ancla(),
        codename="segu_roles_vieja",
        name="Vieja",
    )
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=viejo.id)

    salida = _correr()

    assert "EN USO" in salida


def test_le_arma_la_funcionalidad_al_permiso(db, pantalla_roles):
    _correr()

    acciones = modulos.listar_funcionalidades_de(pantalla_roles.id)

    assert {a.auth_permission.codename for a in acciones} >= {
        "segu_roles_crear_rol",
        "segu_roles_asignar_rol",
    }


def test_avisa_si_falta_la_pantalla_pero_crea_el_permiso_igual(db, activo):
    salida = _correr()

    assert "No existe el Sub_Modulo 'SEGU_ROLES'" in salida
    assert Permission.objects.filter(
        content_type=content_type_del_ancla(),
        codename="segu_roles_crear_rol",
    ).exists()


def test_el_permiso_generado_lo_entiende_has_perm(
    db, pantalla_roles, activo, empresa_a
):
    from django.contrib.auth import get_user_model

    from comun.membresias import api as membresias

    _correr()
    permiso = Permission.objects.get(
        content_type=content_type_del_ancla(),
        codename="segu_roles_asignar_rol",
    )

    juan = get_user_model().objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )
    m = membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=permiso.id)
        seguridad.asignar_rol(
            membresia_id=m.id, grupo_id=rol.id, estado_id=activo.id
        )

        assert juan.has_perm("seguridad.segu_roles_asignar_rol")
