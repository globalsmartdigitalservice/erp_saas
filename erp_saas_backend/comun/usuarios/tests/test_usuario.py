import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction

pytestmark = pytest.mark.django_db

Usuario = get_user_model()


def test_el_modelo_de_usuarios_es_el_nuestro():
    assert Usuario._meta.db_table == "segu_usuario"
    assert Usuario._meta.label == "usuarios.Usuario"


def test_el_usuario_no_tiene_empresa():
    campos = {f.name for f in Usuario._meta.get_fields()}
    assert "empresa" not in campos


def test_el_correo_es_unico():
    Usuario.objects.create_user(
        username="juan", email="juan@acme.com", password="Kx7pLm9Qw2"
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Usuario.objects.create_user(
                username="otro", email="juan@acme.com", password="Kx7pLm9Qw2"
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


def test_la_contrasena_se_guarda_hasheada():
    usuario = Usuario.objects.create_user(
        username="juan", email="juan@acme.com", password="Kx7pLm9Qw2"
    )

    assert "Kx7pLm9Qw2" not in usuario.password
    assert usuario.check_password("Kx7pLm9Qw2")
    assert not usuario.check_password("otra cosa")
