import pytest
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from comun.membresias import api as membresias
from core.tenancy import empresa
from dominios.seguridad import api as seguridad

pytestmark = pytest.mark.django_db

Usuario = get_user_model()


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def juan(empresa_a):
    return Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )


@pytest.fixture
def permiso(db):
    tipo = ContentType.objects.get_for_model(Permission)

    def _permiso(codename):
        p = Permission.objects.create(
            codename=codename, name=codename, content_type=tipo
        )
        return p, f"{tipo.app_label}.{codename}"

    return _permiso


@pytest.fixture
def cadena(crear_empresa, empresa_a):
    """La empresa de Juan con dos sucursales: una cuenta solo trabaja en
    empresas de su propio cliente."""
    norte = crear_empresa("Sucursal Norte", padre=empresa_a)
    sur = crear_empresa("Sucursal Sur", padre=empresa_a)
    return empresa_a, norte, sur


@pytest.fixture
def dar_rol(activo, permiso):
    """Afilia a alguien a una empresa y le da un rol con un permiso."""

    def _dar(usuario, la_empresa, nombre_rol, codename):
        p, codigo = permiso(codename)
        m = membresias.afiliar(
            usuario_id=usuario.id, empresa_id=la_empresa.id, estado_id=activo.id
        )
        with empresa(la_empresa.id):
            rol = seguridad.crear_rol(nombre=nombre_rol, estado_id=activo.id)
            seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=p.id)
            seguridad.asignar_rol(
                membresia_id=m.id, grupo_id=rol.id, estado_id=activo.id
            )
        return codigo

    return _dar


def test_has_perm_ve_los_permisos_del_rol(juan, empresa_a, dar_rol):
    codigo = dar_rol(juan, empresa_a, "Cajero", "emitir_factura")

    with empresa(empresa_a.id):
        assert juan.has_perm(codigo)


def test_sin_rol_no_hay_permiso(juan, empresa_a, activo, permiso):
    _, codigo = permiso("emitir_factura")
    membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )

    with empresa(empresa_a.id):
        assert not juan.has_perm(codigo)


def test_el_permiso_de_una_empresa_no_vale_en_la_otra(juan, empresa_a, sucursal_a, dar_rol, activo):
    codigo = dar_rol(juan, empresa_a, "Cajero", "emitir_factura")
    membresias.afiliar(
        usuario_id=juan.id, empresa_id=sucursal_a.id, estado_id=activo.id
    )

    with empresa(empresa_a.id):
        assert juan.has_perm(codigo)

    juan_otra_vez = Usuario.objects.get(pk=juan.pk)
    with empresa(sucursal_a.id):
        assert not juan_otra_vez.has_perm(codigo)


def test_sin_empresa_elegida_no_hay_permisos(juan, empresa_a, dar_rol):
    codigo = dar_rol(juan, empresa_a, "Cajero", "emitir_factura")

    assert not juan.has_perm(codigo)


def test_el_que_no_trabaja_en_esa_empresa_no_tiene_permisos(
    juan, empresa_a, empresa_b, dar_rol
):
    codigo = dar_rol(juan, empresa_a, "Cajero", "emitir_factura")

    with empresa(empresa_b.id):
        assert not juan.has_perm(codigo)


def test_el_usuario_dado_de_baja_no_tiene_ningun_permiso(juan, empresa_a, dar_rol):
    codigo = dar_rol(juan, empresa_a, "Cajero", "emitir_factura")
    juan.is_active = False

    with empresa(empresa_a.id):
        assert not juan.has_perm(codigo)


def test_el_superusuario_tiene_todo(empresa_a, permiso):
    _, codigo = permiso("emitir_factura")
    staff = Usuario.objects.create_superuser(
        username="admin", email="admin@proveedor.com", password="Zq4tRn8Vd3"
    )

    with empresa(empresa_a.id):
        assert staff.has_perm(codigo)


def test_auth_group_no_da_permisos(juan, empresa_a, activo, permiso):
    from django.contrib.auth.models import Group

    p, codigo = permiso("emitir_factura")
    grupo_django = Group.objects.create(name="Vendedores de toda la instalación")
    grupo_django.permissions.add(p)
    juan.groups.add(grupo_django)
    membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )

    with empresa(empresa_a.id):
        assert not juan.has_perm(codigo)


def test_al_cambiar_de_empresa_los_permisos_se_recalculan(juan, cadena, dar_rol):
    """`ModelBackend` cachea los permisos en un atributo que NO sabe de
    empresas: al cambiar de sucursal se llevaría los permisos de la anterior,
    sin ningún error."""
    _, norte, sur = cadena
    solo_en_norte = dar_rol(juan, norte, "Cajero", "anular_venta")
    dar_rol(juan, sur, "Repositor", "ver_stock")

    with empresa(norte.id):
        assert juan.has_perm(solo_en_norte)

    # MISMO objeto usuario, sin volver a leerlo de la base: es lo que
    # pasa dentro de una request que cambia de empresa.
    with empresa(sur.id):
        assert not juan.has_perm(solo_en_norte)

    # Y de vuelta, para comprobar que el caché no quedó pisado.
    with empresa(norte.id):
        assert juan.has_perm(solo_en_norte)


def test_el_cache_sirve_para_algo(juan, empresa_a, dar_rol):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    codigo = dar_rol(juan, empresa_a, "Cajero", "emitir_factura")

    with empresa(empresa_a.id):
        juan.has_perm(codigo)
        with CaptureQueriesContext(connection) as segunda:
            juan.has_perm(codigo)

    assert len(segunda) == 0


def test_entra_por_nombre_de_usuario(juan):
    assert authenticate(username="juan", password="Kx7pLm9Qw2") == juan


def test_entra_por_correo(juan):
    assert authenticate(username="juan@acme.com", password="Kx7pLm9Qw2") == juan


def test_el_correo_no_distingue_mayusculas(juan):
    assert authenticate(username="JUAN@ACME.COM", password="Kx7pLm9Qw2") == juan


def test_no_entra_con_la_contrasena_equivocada(juan):
    assert authenticate(username="juan", password="otra cosa") is None


def test_no_entra_un_usuario_dado_de_baja(juan):
    juan.is_active = False
    juan.save(update_fields=["is_active"])

    assert authenticate(username="juan", password="Kx7pLm9Qw2") is None


def test_un_usuario_que_no_existe_no_entra(db):
    assert authenticate(username="nadie@acme.com", password="Kx7pLm9Qw2") is None


def test_si_el_texto_es_de_dos_personas_no_entra_ninguna(juan, empresa_a):
    Usuario.objects.create_user(
        username="juan@acme.com",
        email="otra@acme.com",
        password="Zq4tRn8Vd3",
        matriz=empresa_a,
    )

    assert authenticate(username="juan@acme.com", password="Kx7pLm9Qw2") is None
    assert authenticate(username="juan@acme.com", password="Zq4tRn8Vd3") is None
