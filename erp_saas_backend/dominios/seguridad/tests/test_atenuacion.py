import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError

from core.tenancy import empresa
from core.tests.afiliacion import afiliar_en
from dominios.seguridad import api as seguridad
from dominios.seguridad.permisos import content_type_del_ancla

pytestmark = pytest.mark.django_db

Usuario = get_user_model()


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def permiso(db):
    def _permiso(codename):
        return Permission.objects.get_or_create(
            content_type=content_type_del_ancla(),
            codename=codename,
            defaults={"name": codename},
        )[0]

    return _permiso


def _codigo(permiso):
    return f"{permiso.content_type.app_label}.{permiso.codename}"


def test_no_se_agrega_al_rol_un_permiso_que_no_se_tiene(empresa_a, activo, permiso):
    anular = permiso("vent_facturas_anular")

    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

        with pytest.raises(ValidationError, match="no tiene ese permiso"):
            seguridad.agregar_permiso(
                grupo_id=rol.id, auth_permission_id=anular.id, otorgables=set()
            )


def test_se_agrega_al_rol_un_permiso_que_si_se_tiene(empresa_a, activo, permiso):
    anular = permiso("vent_facturas_anular")

    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        lineas = seguridad.agregar_permiso(
            grupo_id=rol.id,
            auth_permission_id=anular.id,
            otorgables={_codigo(anular)},
        )

    assert [linea.auth_permission_id for linea in lineas] == [anular.id]


def test_sin_limite_se_agrega_cualquier_permiso(empresa_a, activo, permiso):
    anular = permiso("vent_facturas_anular")

    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        lineas = seguridad.agregar_permiso(
            grupo_id=rol.id, auth_permission_id=anular.id, otorgables=None
        )

    assert len(lineas) == 1


def test_no_se_asigna_un_rol_con_permisos_que_no_se_tienen(
    empresa_a, activo, permiso, crear_empresa
):
    anular = permiso("vent_facturas_anular")
    juan = Usuario.objects.create_user(
        username="juan", email="juan@acme.com", password="Kx7pLm9Qw2", matriz=empresa_a
    )

    with empresa(empresa_a.id):
        membresia = afiliar_en(empresa_a.id, usuario_id=juan.id, estado_id=activo.id)
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=anular.id)

        with pytest.raises(ValidationError, match="permisos que usted no tiene"):
            seguridad.asignar_rol(
                membresia_id=membresia.id,
                grupo_id=rol.id,
                estado_id=activo.id,
                otorgables=set(),
            )


def test_se_asigna_el_rol_cuando_se_tienen_todos_sus_permisos(
    empresa_a, activo, permiso
):
    anular = permiso("vent_facturas_anular")
    juan = Usuario.objects.create_user(
        username="juan", email="juan@acme.com", password="Kx7pLm9Qw2", matriz=empresa_a
    )

    with empresa(empresa_a.id):
        membresia = afiliar_en(empresa_a.id, usuario_id=juan.id, estado_id=activo.id)
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=anular.id)

        asignacion = seguridad.asignar_rol(
            membresia_id=membresia.id,
            grupo_id=rol.id,
            estado_id=activo.id,
            otorgables={_codigo(anular)},
        )

    assert asignacion.grupo_empresa_id == rol.id


def test_un_rol_sin_permisos_se_asigna_siempre(empresa_a, activo):
    juan = Usuario.objects.create_user(
        username="juan", email="juan@acme.com", password="Kx7pLm9Qw2", matriz=empresa_a
    )

    with empresa(empresa_a.id):
        membresia = afiliar_en(empresa_a.id, usuario_id=juan.id, estado_id=activo.id)
        rol = seguridad.crear_rol(nombre="Sin permisos", estado_id=activo.id)

        asignacion = seguridad.asignar_rol(
            membresia_id=membresia.id,
            grupo_id=rol.id,
            estado_id=activo.id,
            otorgables=set(),
        )

    assert asignacion.grupo_empresa_id == rol.id
