import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction

from comun.usuarios import api as usuarios
from core.tenancy import empresa

pytestmark = pytest.mark.django_db

Usuario = get_user_model()


def test_el_modelo_de_usuarios_es_el_nuestro():
    assert Usuario._meta.db_table == "segu_usuario"
    assert Usuario._meta.label == "usuarios.Usuario"


def test_la_cuenta_es_de_un_cliente_y_no_de_una_empresa():
    """La cuenta pertenece a la MATRIZ; en qué empresas trabaja lo dice
    `Usuario_Empresa`."""
    campos = {f.name for f in Usuario._meta.get_fields()}
    assert "empresa" not in campos
    assert "matriz" in campos


def test_el_correo_es_unico_DENTRO_del_cliente(empresa_a):
    Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Usuario.objects.create_user(
                username="otro",
                email="juan@acme.com",
                password="Kx7pLm9Qw2",
                matriz=empresa_a,
            )


def test_el_mismo_correo_puede_estar_en_dos_clientes(empresa_a, empresa_b):
    """Juan trabaja en el gimnasio y en la farmacia con su único correo.

    Es lo que antes obligaba a decirle al segundo administrador que esa
    persona ya existía en otro cliente."""
    Usuario.objects.create_user(
        username="juan.gimnasio",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )

    juan_farmacia = Usuario.objects.create_user(
        username="juan.farmacia",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_b,
    )

    assert juan_farmacia.pk is not None


def test_el_correo_no_se_repite_cambiando_las_mayusculas(empresa_a):
    """Para una persona es el mismo correo; para la base son dos textos."""
    Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Usuario.objects.create_user(
                username="otro",
                email="JUAN@ACME.COM",
                password="Kx7pLm9Qw2",
                matriz=empresa_a,
            )


def test_el_nombre_de_usuario_no_puede_llevar_arroba(empresa_a):
    """Con `@` no se puede distinguir un usuario de un correo, y el login
    necesita esa diferencia para saber si puede haber varias cuentas."""
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="arroba"):
            usuarios.crear_usuario(
                username="juan@acme.com",
                email="juan@acme.com",
                password="Kx7pLm9Qw2",
            )


def test_el_correo_es_obligatorio():
    usuario = Usuario(username="juan", email="")

    with pytest.raises(ValidationError) as e:
        usuario.full_clean()

    assert "email" in e.value.message_dict


def test_el_nombre_completo_incluye_el_apellido_materno():
    usuario = Usuario(
        username="jvillarroel",
        first_name="Juan Carlos",
        last_name="Villarroel",
        seg_apellido="Mamani",
    )

    assert usuario.get_full_name() == "Juan Carlos Villarroel Mamani"


def test_con_un_solo_apellido_no_queda_un_espacio_colgando():
    usuario = Usuario(username="acruz", first_name="Ana", last_name="Cruz")

    assert usuario.get_full_name() == "Ana Cruz"


def test_el_apellido_materno_no_sirve_de_contrasena():
    """`UserAttributeSimilarityValidator` lee cada campo con
    `getattr(..., None)`: `seg_apellido` no está en su lista interna, así que
    sin el `OPTIONS` de settings NO lo revisa, sin error ni log."""
    usuario = Usuario(
        username="jvillarroel",
        email="juan@acme.com",
        first_name="Juan",
        last_name="Villarroel",
        seg_apellido="Mamani",
    )

    with pytest.raises(ValidationError):
        validate_password("Mamani2026", usuario)


@pytest.mark.parametrize(
    "clave, de_donde_sale",
    [
        ("jvillarroel1", "el usuario"),
        ("Villarroel26", "el apellido paterno"),
        ("Mamani2026", "el apellido materno"),
        ("juan@acme.com1", "el correo"),
    ],
)
def test_la_contrasena_no_puede_parecerse_a_los_datos_propios(clave, de_donde_sale):
    usuario = Usuario(
        username="jvillarroel",
        email="juan@acme.com",
        first_name="Juan",
        last_name="Villarroel",
        seg_apellido="Mamani",
    )

    with pytest.raises(ValidationError):
        validate_password(clave, usuario)


def test_la_contrasena_se_guarda_hasheada(empresa_a):
    usuario = Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )

    assert "Kx7pLm9Qw2" not in usuario.password
    assert usuario.check_password("Kx7pLm9Qw2")
    assert not usuario.check_password("otra cosa")


@pytest.fixture
def beto_de_la_farmacia(empresa_b):
    """Alguien de OTRO cliente."""
    return Usuario.objects.create_user(
        username="beto",
        email="beto@farmacia.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_b,
    )


def test_no_se_edita_la_cuenta_de_OTRO_cliente(empresa_a, beto_de_la_farmacia):
    """El más grave de los tres: el correo es por donde se resetea la
    contraseña. Quien le cambia el correo a alguien, le roba la cuenta."""
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError):
            usuarios.actualizar_usuario(
                beto_de_la_farmacia.id, email="beto@ahora-es-mio.com"
            )

    beto_de_la_farmacia.refresh_from_db()
    assert beto_de_la_farmacia.email == "beto@farmacia.com"


def test_no_se_da_de_baja_la_cuenta_de_OTRO_cliente(empresa_a, beto_de_la_farmacia):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError):
            usuarios.desactivar_usuario(beto_de_la_farmacia.id)

    beto_de_la_farmacia.refresh_from_db()
    assert beto_de_la_farmacia.is_active


def test_no_se_lee_la_cuenta_de_OTRO_cliente(empresa_a, beto_de_la_farmacia):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError):
            usuarios.obtener_usuario_del_cliente(beto_de_la_farmacia.id)


def test_el_rechazo_no_delata_si_la_cuenta_existe(empresa_a, beto_de_la_farmacia):
    """Decir 'no tiene permiso sobre el usuario 7' confirma que el 7 existe."""
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError) as ajena:
            usuarios.obtener_usuario_del_cliente(beto_de_la_farmacia.id)

        with pytest.raises(ValidationError) as inexistente:
            usuarios.obtener_usuario_del_cliente(999999)

    assert ajena.value.messages[0].replace(
        str(beto_de_la_farmacia.id), "N"
    ) == inexistente.value.messages[0].replace("999999", "N")


def test_SI_se_edita_la_cuenta_del_propio_cliente(empresa_a):
    """Lo que tiene que seguir funcionando."""
    with empresa(empresa_a.id):
        ana = usuarios.crear_usuario(
            username="ana", email="ana@gimnasio.com", password="Kx7pLm9Qw2"
        )

        usuarios.actualizar_usuario(ana.id, email="ana@nuevo.com")

    ana.refresh_from_db()
    assert ana.email == "ana@nuevo.com"
