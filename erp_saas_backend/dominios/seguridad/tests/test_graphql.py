import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext

from comun.catalogo_modulos import api as modulos
from comun.membresias import api as membresias
from config.schema import schema
from core.tenancy import empresa
from core.tests.afiliacion import afiliar_en
from core.tests.contexto_graphql import Contexto
from dominios.seguridad.models import GrupoUsuario

pytestmark = pytest.mark.django_db

Usuario = get_user_model()


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


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

    def _permiso(codename, nombre=None):
        return Permission.objects.create(
            codename=codename, name=nombre or codename, content_type=tipo
        )

    return _permiso


# Superusuario a propósito: acá se prueban los resolvers y el batch de
# consultas, no la autorización. Eso está en `test_guards.py`.


# Lo llena la fixture de abajo. Un módulo global y no un parámetro para
# no tener que pasarlo por las ~20 llamadas de este archivo.
_COMO = {}


@pytest.fixture(autouse=True)
def como_superusuario(db):
    _COMO["usuario"] = Usuario.objects.create_superuser(
        username="prueba_admin",
        email="admin@prueba.com",
        password="Zq4tRn8Vd3",
    )
    yield
    _COMO.clear()


def _correr(consulta, **variables):
    resultado = schema.execute_sync(
        consulta,
        variable_values=variables or None,
        context_value=Contexto(_COMO["usuario"]),
    )
    assert resultado.errors is None, resultado.errors
    return resultado.data


def test_el_usuario_no_expone_la_contrasena(db):
    resultado = schema.execute_sync("{ usuario(id: \"1\") { password } }")

    assert resultado.errors is not None


def test_afiliar_al_grupo_y_ver_el_selector(cadena, activo):
    matriz, _, _ = cadena
    jose = Usuario.objects.create_user(
        username="jose",
        email="jose@acme.com",
        password="Kx7pLm9Qw2",
        matriz=matriz,
    )

    with empresa(matriz.id):
        creadas = _correr(
            """
            mutation ($datos: AfiliarInput!) {
              afiliarAlGrupo(datos: $datos) { id }
            }
            """,
            datos={
                "usuarioId": str(jose.id),
                "estadoId": str(activo.id),
            },
        )["afiliarAlGrupo"]

    assert len(creadas) == 3

    #  El selector del login ya no sale de una consulta: `empresasDelUsuario`
    # se borró porque decía en qué empresas trabaja alguien sin pedir sesión.
    # La lista viaja en la respuesta de `login`.


def test_los_miembros_son_solo_los_de_la_empresa_activa(cadena, activo):
    matriz, norte, _ = cadena
    jose = Usuario.objects.create_user(
        username="jose",
        email="jose@acme.com",
        password="Kx7pLm9Qw2",
        matriz=matriz,
    )
    ana = Usuario.objects.create_user(
        username="ana",
        email="ana@acme.com",
        password="Zq4tRn8Vd3",
        matriz=matriz,
    )
    afiliar_en(matriz.id, usuario_id=jose.id, estado_id=activo.id)
    afiliar_en(norte.id, usuario_id=ana.id, estado_id=activo.id)

    with empresa(matriz.id):
        datos = _correr("{ miembros { usuario { username } } }")

    assert [m["usuario"]["username"] for m in datos["miembros"]] == ["jose"]


def test_la_lista_de_miembros_no_dispara_una_consulta_por_persona(
    empresa_a, activo, django_assert_max_num_queries
):
    for i in range(10):
        u = Usuario.objects.create_user(
            username=f"u{i}",
            email=f"u{i}@acme.com",
            password="Kx7pLm9Qw2",
            matriz=empresa_a,
        )
        afiliar_en(empresa_a.id, usuario_id=u.id, estado_id=activo.id)

    with empresa(empresa_a.id):
        # 1 membresías + 1 usuarios por lote
        with django_assert_max_num_queries(2):
            datos = _correr("{ miembros { usuario { username } } }")

    assert len(datos["miembros"]) == 10


def test_el_recorrido_completo(cadena, activo, permiso):
    matriz, norte, _ = cadena
    p = permiso("anular_factura", "Anular factura")

    jose = Usuario.objects.create_user(
        username="jose",
        email="jose@acme.com",
        password="Kx7pLm9Qw2",
        matriz=matriz,
    )

    with empresa(matriz.id):
        _correr(
            "mutation ($d: AfiliarInput!) { afiliarAlGrupo(datos: $d) { id } }",
            d={
                "usuarioId": str(jose.id),
                "estadoId": str(activo.id),
            },
        )

    # 3 — la matriz arma el rol
    with empresa(matriz.id):
        rol = _correr(
            "mutation ($d: CrearRolInput!) { crearRol(datos: $d) { id nombre esHeredado } }",
            d={"nombre": "Cajero", "estadoId": str(activo.id)},
        )["crearRol"]
        assert rol["esHeredado"] is False

        _correr(
            """
            mutation ($rol: ID!, $permiso: ID!) {
              agregarPermisoAlRol(rolId: $rol, authPermissionId: $permiso) {
                codigo etiqueta
              }
            }
            """,
            rol=rol["id"],
            permiso=str(p.id),
        )

    # 4 — la sucursal lo VE, marcado como heredado
    with empresa(norte.id):
        roles = _correr("{ roles { id nombre esHeredado cantidadPermisos } }")["roles"]
        assert len(roles) == 1
        assert roles[0]["esHeredado"] is True
        assert roles[0]["cantidadPermisos"] == 1

        # ...y ve sus permisos: si esta tabla se hubiera hecho con el
        # filtro por empresa exacta, acá vendría vacío.
        permisos = _correr(
            "query ($id: ID!) { permisosDelRol(rolId: $id) { codigo } }", id=rol["id"]
        )["permisosDelRol"]
        assert len(permisos) == 1

        # ...pero NO lo puede editar
        fallo = schema.execute_sync(
            "mutation ($id: ID!, $d: ActualizarRolInput!) "
            "{ actualizarRol(id: $id, datos: $d) { nombre } }",
            variable_values={"id": rol["id"], "d": {"nombre": "Otro nombre"}},
            # Con contexto: lo que se prueba acá es la regla de la casa
            # matriz, no la autorización. Sin él, el guard rechazaría
            # antes y el test verificaría otra cosa.
            context_value=Contexto(_COMO["usuario"]),
        )
        assert fallo.errors is not None
        assert "casa matriz" in str(fallo.errors[0].message)

        # 5 — y se lo asigna a Don José
        suya = _correr(
            "query ($u: ID!) { membresia(usuarioId: $u) { id } }", u=str(jose.id)
        )["membresia"]

        _correr(
            "mutation ($d: AsignarRolInput!) { asignarRol(datos: $d) { id motivo } }",
            d={
                "membresiaId": suya["id"],
                "rolId": rol["id"],
                "estadoId": str(activo.id),
                "motivo": "gerente de la cadena",
            },
        )

        # 6 — y ahora sí puede
        mis = _correr(
            "query ($m: ID!) { permisosDe(membresiaId: $m) }", m=suya["id"]
        )["permisosDe"]

    assert mis == [f"{p.content_type.app_label}.anular_factura"]

    # Y coincide con lo que contesta has_perm(), que es lo que de verdad
    # decide en el backend.
    persona = Usuario.objects.get(pk=jose.id)
    with empresa(norte.id):
        assert persona.has_perm(mis[0])


def test_la_asignacion_de_rol_guarda_quien_la_hizo(empresa_a, activo):
    """El autor sale de la sesión, no del input. La falla sería SILENCIOSA:
    sin el dato la fila se crea igual, la mutation devuelve su id, y recién se
    descubre al auditar quién le dio ese rol a quién."""
    jose = Usuario.objects.create_user(
        username="jose",
        email="jose@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )
    suya = afiliar_en(empresa_a.id, usuario_id=jose.id, estado_id=activo.id)

    with empresa(empresa_a.id):
        rol = _correr(
            "mutation ($d: CrearRolInput!) { crearRol(datos: $d) { id } }",
            d={"nombre": "Cajero", "estadoId": str(activo.id)},
        )["crearRol"]
        asignada = _correr(
            "mutation ($d: AsignarRolInput!) { asignarRol(datos: $d) { id } }",
            d={
                "membresiaId": str(suya.id),
                "rolId": rol["id"],
                "estadoId": str(activo.id),
            },
        )["asignarRol"]

        fila = GrupoUsuario.objects.get(pk=int(asignada["id"]))

    assert fila.asignado_por_id == _COMO["usuario"].pk


def test_el_arbol_de_pantallas_trae_sus_acciones(activo, permiso):
    ventas = modulos.crear(codigo="VENTAS", nombre="Ventas", estado_id=activo.id)
    facturas = modulos.crear_sub_modulo(
        codigo="VENTAS_FACTURAS",
        modulo_sistema_id=ventas.id,
        nombre="Facturas",
        ruta="/ventas/facturas",
        estado_id=activo.id,
    )
    for nombre, code in [("Emitir", "emitir_f"), ("Anular", "anular_f")]:
        modulos.crear_funcionalidad(
            sub_modulo_id=facturas.id,
            auth_permission_id=permiso(code).id,
            nombre=nombre,
            estado_id=activo.id,
        )

    datos = _correr("{ subModulos { codigo ruta funcionalidades { nombre } } }")

    pantalla = datos["subModulos"][0]
    assert pantalla["ruta"] == "/ventas/facturas"
    assert {f["nombre"] for f in pantalla["funcionalidades"]} == {"Emitir", "Anular"}


def test_el_arbol_no_dispara_una_consulta_por_pantalla(activo, permiso):
    ventas = modulos.crear(codigo="VENTAS", nombre="Ventas", estado_id=activo.id)

    def costo():
        with CaptureQueriesContext(connection) as capturadas:
            _correr("{ subModulos { codigo funcionalidades { nombre } } }")
        return len(capturadas)

    modulos.crear_sub_modulo(
        codigo="P0",
        modulo_sistema_id=ventas.id,
        nombre="Pantalla 0",
        ruta="/p0",
        estado_id=activo.id,
    )
    con_una = costo()

    for i in range(1, 10):
        pantalla = modulos.crear_sub_modulo(
            codigo=f"P{i}",
            modulo_sistema_id=ventas.id,
            nombre=f"Pantalla {i}",
            ruta=f"/p{i}",
            estado_id=activo.id,
        )
        modulos.crear_funcionalidad(
            sub_modulo_id=pantalla.id,
            auth_permission_id=permiso(f"accion_{i}").id,
            nombre=f"Acción {i}",
            estado_id=activo.id,
        )

    assert costo() == con_una
