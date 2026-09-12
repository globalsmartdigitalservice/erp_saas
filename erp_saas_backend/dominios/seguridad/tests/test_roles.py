import datetime

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from comun.membresias import api as membresias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from core.tenancy import SinEmpresaEnContexto, empresa
from dominios.seguridad import api as seguridad

pytestmark = pytest.mark.django_db

Usuario = get_user_model()


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def de_baja(catalogo):
    return catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)


@pytest.fixture
def cadena(crear_empresa, empresa_a):
    """La empresa de Juan con dos sucursales: una cuenta solo trabaja en
    empresas de su propio cliente."""
    norte = crear_empresa("Sucursal Norte", padre=empresa_a)
    sur = crear_empresa("Sucursal Sur", padre=empresa_a)
    return empresa_a, norte, sur


@pytest.fixture
def permiso(db):
    tipo = ContentType.objects.get_for_model(Permission)
    contador = {"n": 0}

    def _permiso(codename=None):
        contador["n"] += 1
        codename = codename or f"permiso_{contador['n']}"
        return Permission.objects.create(
            codename=codename, name=codename, content_type=tipo
        )

    return _permiso


@pytest.fixture
def afiliar(activo):
    def _afiliar(usuario, la_empresa):
        return membresias.afiliar(
            usuario_id=usuario.id, empresa_id=la_empresa.id, estado_id=activo.id
        )

    return _afiliar


@pytest.fixture
def juan(empresa_a):
    return Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )


def test_el_rol_se_crea_en_la_empresa_activa(empresa_a, activo):
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    assert rol.empresa_id == empresa_a.id


def test_sin_empresa_en_el_contexto_no_se_pueden_ver_los_roles(empresa_a, activo):
    with empresa(empresa_a.id):
        seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    with pytest.raises(SinEmpresaEnContexto):
        seguridad.listar_roles()


def test_otro_cliente_no_ve_el_rol(empresa_a, empresa_b, activo):
    with empresa(empresa_a.id):
        seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    with empresa(empresa_b.id):
        assert seguridad.listar_roles() == []


def test_la_sucursal_ve_el_rol_de_su_matriz(cadena, activo):
    matriz, norte, _ = cadena
    with empresa(matriz.id):
        seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    with empresa(norte.id):
        assert [r.nombre for r in seguridad.listar_roles()] == ["Cajero"]


def test_la_herencia_no_sube(cadena, activo):
    matriz, norte, _ = cadena
    with empresa(norte.id):
        seguridad.crear_rol(nombre="Repositor", estado_id=activo.id)

    with empresa(matriz.id):
        assert seguridad.listar_roles() == []


def test_la_herencia_no_cruza_entre_sucursales(cadena, activo):
    _, norte, sur = cadena
    with empresa(norte.id):
        seguridad.crear_rol(nombre="Repositor", estado_id=activo.id)

    with empresa(sur.id):
        assert seguridad.listar_roles() == []


def test_la_sucursal_no_puede_editar_el_rol_de_la_matriz(cadena, activo):
    matriz, norte, _ = cadena
    with empresa(matriz.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    with empresa(norte.id):
        with pytest.raises(ValidationError, match="casa matriz"):
            seguridad.actualizar_rol(rol.id, nombre="Cajero modificado")


def test_la_sucursal_no_puede_tocar_los_permisos_del_rol_heredado(
    cadena, activo, permiso
):
    matriz, norte, _ = cadena
    with empresa(matriz.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    with empresa(norte.id):
        with pytest.raises(ValidationError, match="casa matriz"):
            seguridad.agregar_permiso(
                grupo_id=rol.id, auth_permission_id=permiso().id
            )


def test_la_sucursal_si_puede_con_lo_suyo(cadena, activo):
    _, norte, _ = cadena
    with empresa(norte.id):
        propio = seguridad.crear_rol(nombre="Repositor", estado_id=activo.id)
        editado = seguridad.actualizar_rol(propio.id, nombre="Repositor de turno")

    assert editado.nombre == "Repositor de turno"


def test_la_sucursal_no_repite_un_nombre_que_ya_hereda(cadena, activo):
    matriz, norte, _ = cadena
    with empresa(matriz.id):
        seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    with empresa(norte.id):
        with pytest.raises(ValidationError, match="Ya puede usar un rol"):
            seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)


def test_agregar_permiso_es_idempotente(empresa_a, activo, permiso):
    p = permiso("anular_factura")
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=p.id)
        lineas = seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=p.id)

    assert len(lineas) == 1


def test_quitar_un_permiso_que_no_estaba_no_falla(empresa_a, activo, permiso):
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        assert seguridad.quitar_permiso(
            grupo_id=rol.id, auth_permission_id=permiso().id
        ) == []


def test_la_sucursal_ve_los_permisos_del_rol_heredado(cadena, activo, permiso):
    """Con `ModeloTenantDerivado` esto daría CERO permisos: la sucursal vería
    el rol "Cajero" vacío, sin ningún error."""
    matriz, norte, _ = cadena
    with empresa(matriz.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(
            grupo_id=rol.id, auth_permission_id=permiso("emitir_factura").id
        )
        seguridad.agregar_permiso(
            grupo_id=rol.id, auth_permission_id=permiso("cobrar").id
        )

    with empresa(norte.id):
        assert len(seguridad.listar_permisos_del_rol(rol.id)) == 2


def test_otro_cliente_no_ve_los_permisos_del_rol(empresa_a, empresa_b, activo, permiso):
    with empresa(empresa_a.id):
        rol_a = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(
            grupo_id=rol_a.id, auth_permission_id=permiso("emitir_factura").id
        )

    with empresa(empresa_b.id):
        assert seguridad.listar_permisos_del_rol(rol_a.id) == []


def test_el_manager_de_los_permisos_no_los_muestra_todos(
    empresa_a, empresa_b, activo, permiso
):
    from dominios.seguridad.models import GrupoEmpresaPermiso

    with empresa(empresa_a.id):
        rol_a = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(
            grupo_id=rol_a.id, auth_permission_id=permiso("emitir_factura").id
        )

    with empresa(empresa_b.id):
        rol_b = seguridad.crear_rol(nombre="Vendedor", estado_id=activo.id)
        seguridad.agregar_permiso(
            grupo_id=rol_b.id, auth_permission_id=permiso("ver_stock").id
        )
        visibles = list(GrupoEmpresaPermiso.objects.all())

    assert [linea.grupo_empresa_id for linea in visibles] == [rol_b.id]


def test_asignar_un_rol_de_la_matriz_a_alguien_de_la_sucursal(
    cadena, juan, afiliar, activo
):
    matriz, norte, _ = cadena
    with empresa(matriz.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    membresia = afiliar(juan, norte)
    with empresa(norte.id):
        asignacion = seguridad.asignar_rol(
            membresia_id=membresia.id, grupo_id=rol.id, estado_id=activo.id
        )

    assert asignacion.grupo_empresa_id == rol.id
    assert asignacion.usuario_empresa_id == membresia.id


def test_no_se_puede_asignar_el_rol_de_otro_cliente(
    empresa_a, empresa_b, juan, afiliar, activo
):
    with empresa(empresa_b.id):
        rol_ajeno = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)

    membresia = afiliar(juan, empresa_a)
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="no está disponible"):
            seguridad.asignar_rol(
                membresia_id=membresia.id, grupo_id=rol_ajeno.id, estado_id=activo.id
            )


def test_el_mensaje_no_delata_si_el_id_existe(empresa_a, juan, afiliar, activo):
    membresia = afiliar(juan, empresa_a)
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="no está disponible"):
            seguridad.asignar_rol(
                membresia_id=membresia.id, grupo_id=999999, estado_id=activo.id
            )


def test_no_se_asigna_dos_veces_el_mismo_rol_vigente(
    empresa_a, juan, afiliar, activo
):
    membresia = afiliar(juan, empresa_a)
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.asignar_rol(
            membresia_id=membresia.id, grupo_id=rol.id, estado_id=activo.id
        )

        with pytest.raises(ValidationError, match="ya tiene ese rol vigente"):
            seguridad.asignar_rol(
                membresia_id=membresia.id, grupo_id=rol.id, estado_id=activo.id
            )


def test_el_mismo_rol_si_se_puede_volver_a_dar_despues_de_quitarlo(
    empresa_a, juan, afiliar, activo, de_baja
):
    membresia = afiliar(juan, empresa_a)
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        primera = seguridad.asignar_rol(
            membresia_id=membresia.id, grupo_id=rol.id, estado_id=activo.id
        )
        seguridad.quitar_rol(asignacion_id=primera.id)
        seguridad.asignar_rol(
            membresia_id=membresia.id, grupo_id=rol.id, estado_id=activo.id
        )

        assert len(seguridad.historial_de(membresia.id)) == 2


def test_quitar_el_rol_no_borra_la_fila(empresa_a, juan, afiliar, activo, de_baja):
    membresia = afiliar(juan, empresa_a)
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        asignacion = seguridad.asignar_rol(
            membresia_id=membresia.id, grupo_id=rol.id, estado_id=activo.id
        )
        quitada = seguridad.quitar_rol(asignacion_id=asignacion.id)

    assert quitada.id == asignacion.id
    assert quitada.fecha_fin == datetime.date.today()
    assert quitada.estado_id == de_baja.id


def test_no_se_da_de_baja_un_rol_que_alguien_tiene(
    empresa_a, juan, afiliar, activo, de_baja
):
    membresia = afiliar(juan, empresa_a)
    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.asignar_rol(
            membresia_id=membresia.id, grupo_id=rol.id, estado_id=activo.id
        )

        with pytest.raises(ValidationError, match="hay gente que lo tiene"):
            seguridad.desactivar_rol(rol.id)


def test_los_permisos_de_una_persona_unen_todos_sus_roles(
    empresa_a, juan, afiliar, activo, permiso
):
    membresia = afiliar(juan, empresa_a)
    with empresa(empresa_a.id):
        cajero = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        supervisor = seguridad.crear_rol(nombre="Supervisor", estado_id=activo.id)
        seguridad.agregar_permiso(
            grupo_id=cajero.id, auth_permission_id=permiso("emitir_factura").id
        )
        seguridad.agregar_permiso(
            grupo_id=supervisor.id, auth_permission_id=permiso("anular_factura").id
        )
        seguridad.asignar_rol(
            membresia_id=membresia.id, grupo_id=cajero.id, estado_id=activo.id
        )
        seguridad.asignar_rol(
            membresia_id=membresia.id, grupo_id=supervisor.id, estado_id=activo.id
        )

        codigos = {c.split(".")[-1] for c in seguridad.permisos_de(membresia.id)}

    assert codigos == {"emitir_factura", "anular_factura"}


def test_un_rol_vencido_ya_no_da_permisos(
    empresa_a, juan, afiliar, activo, permiso
):
    ayer = datetime.date.today() - datetime.timedelta(days=1)
    anteayer = datetime.date.today() - datetime.timedelta(days=2)
    membresia = afiliar(juan, empresa_a)

    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(
            grupo_id=rol.id, auth_permission_id=permiso("emitir_factura").id
        )
        seguridad.asignar_rol(
            membresia_id=membresia.id,
            grupo_id=rol.id,
            estado_id=activo.id,
            fecha_inicio=anteayer,
            fecha_fin=ayer,
        )

        assert seguridad.permisos_de(membresia.id) == set()


def test_un_rol_que_todavia_no_empezo_no_da_permisos(
    empresa_a, juan, afiliar, activo, permiso
):
    manana = datetime.date.today() + datetime.timedelta(days=1)
    membresia = afiliar(juan, empresa_a)

    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        seguridad.agregar_permiso(
            grupo_id=rol.id, auth_permission_id=permiso("emitir_factura").id
        )
        seguridad.asignar_rol(
            membresia_id=membresia.id,
            grupo_id=rol.id,
            estado_id=activo.id,
            fecha_inicio=manana,
        )

        assert seguridad.permisos_de(membresia.id) == set()


def test_la_fecha_de_fin_no_puede_ser_anterior_al_inicio(
    empresa_a, juan, afiliar, activo
):
    ayer = datetime.date.today() - datetime.timedelta(days=1)
    membresia = afiliar(juan, empresa_a)

    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Cajero", estado_id=activo.id)
        with pytest.raises(ValidationError, match="anterior a la de inicio"):
            seguridad.asignar_rol(
                membresia_id=membresia.id,
                grupo_id=rol.id,
                estado_id=activo.id,
                fecha_fin=ayer,
            )


def _consultas_de(fn) -> int:
    """Cuántas consultas cuesta ejecutar `fn`."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as capturadas:
        fn()
    return len(capturadas)


def test_los_permisos_de_una_persona_no_crecen_con_sus_roles(
    empresa_a, empresa_b, juan, afiliar, activo, permiso
):
    ana = Usuario.objects.create_user(
        username="ana",
        email="ana@acme.com",
        password="Zq4tRn8Vd3",
        matriz=empresa_a,
    )
    con_uno = afiliar(juan, empresa_a)
    con_seis = afiliar(ana, empresa_a)

    with empresa(empresa_a.id):
        rol = seguridad.crear_rol(nombre="Rol único", estado_id=activo.id)
        seguridad.agregar_permiso(grupo_id=rol.id, auth_permission_id=permiso().id)
        seguridad.asignar_rol(
            membresia_id=con_uno.id, grupo_id=rol.id, estado_id=activo.id
        )

        for i in range(6):
            otro = seguridad.crear_rol(nombre=f"Rol {i}", estado_id=activo.id)
            seguridad.agregar_permiso(
                grupo_id=otro.id, auth_permission_id=permiso().id
            )
            seguridad.asignar_rol(
                membresia_id=con_seis.id, grupo_id=otro.id, estado_id=activo.id
            )

        costo_uno = _consultas_de(lambda: seguridad.permisos_de(con_uno.id))
        costo_seis = _consultas_de(lambda: seguridad.permisos_de(con_seis.id))

        assert len(seguridad.permisos_de(con_seis.id)) == 6

    assert costo_seis == costo_uno, (
        f"Con 1 rol cuesta {costo_uno} consultas y con 6 cuesta {costo_seis}: "
        f"volvió el N+1. Revisá los `select_related` de "
        f"repository/grupo_empresa.py y repository/grupo_usuario.py."
    )


def test_listar_roles_con_su_conteo_no_crece(empresa_a, activo, permiso):
    with empresa(empresa_a.id):
        primero = seguridad.crear_rol(nombre="Rol 0", estado_id=activo.id)
        seguridad.agregar_permiso(
            grupo_id=primero.id, auth_permission_id=permiso().id
        )

        def leer_todo():
            roles = seguridad.listar_roles_con_conteo()
            # Tocar las relaciones es lo que dispararía el N+1 si faltara.
            [(r.empresa.razon_social, r.cantidad_permisos) for r in roles]
            return roles

        costo_uno = _consultas_de(leer_todo)

        for i in range(1, 20):
            otro = seguridad.crear_rol(nombre=f"Rol {i}", estado_id=activo.id)
            seguridad.agregar_permiso(
                grupo_id=otro.id, auth_permission_id=permiso().id
            )

        costo_veinte = _consultas_de(leer_todo)

        assert len(leer_todo()) == 20

    assert costo_veinte == costo_uno, (
        f"Con 1 rol cuesta {costo_uno} consultas y con 20 cuesta "
        f"{costo_veinte}: volvió el N+1 en listar_con_cantidad_de_permisos."
    )
