import pytest
from django.core.exceptions import ValidationError

from core.tenancy import empresa
from dominios.entidades import api as entidades

pytestmark = pytest.mark.django_db


def test_una_entidad_puede_ser_cliente_y_proveedor(
    empresa_a, crear_entidad, rol_de
):
    with empresa(empresa_a.id):
        ferreteria = crear_entidad("El Tornillo")
        rol_de(ferreteria, "rol_cliente")
        rol_de(ferreteria, "rol_proveedor")

        assert len(entidades.listar_roles_de(ferreteria.pk)) == 2


def test_una_entidad_no_repite_el_mismo_rol(empresa_a, crear_entidad, rol_de):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        rol_de(juan, "rol_cliente")

        with pytest.raises(ValidationError, match="ya tiene ese rol"):
            rol_de(juan, "rol_cliente")


def test_no_se_le_puede_colgar_un_rol_a_la_entidad_de_otra_empresa(
    empresa_a, empresa_b, crear_entidad, rol_de
):
    with empresa(empresa_a.id):
        de_a = crear_entidad("Juan de A")

    with empresa(empresa_b.id):
        with pytest.raises(ValidationError, match="No existe la entidad"):
            rol_de(de_a)


def test_no_se_le_puede_poner_una_categoria_de_otra_empresa(
    empresa_a, empresa_b, crear_entidad, rol_de, crear_categoria
):
    with empresa(empresa_b.id):
        categoria_de_b = crear_categoria()

    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

        with pytest.raises(ValidationError, match="No existe la categoría"):
            rol_de(juan, categoria_entidad_id=categoria_de_b.pk)


def test_el_mensaje_no_delata_que_el_id_existe_en_otra_empresa(
    empresa_a, empresa_b, crear_entidad, rol_de, crear_categoria
):
    with empresa(empresa_b.id):
        categoria_de_b = crear_categoria()

    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

        with pytest.raises(ValidationError) as error:
            rol_de(juan, categoria_entidad_id=categoria_de_b.pk)

    mensaje = str(error.value).lower()
    assert "no existe" in mensaje
    assert "permiso" not in mensaje
    assert "otra empresa" not in mensaje


def test_la_categoria_propia_si_se_puede(
    empresa_a, crear_entidad, rol_de, crear_categoria
):
    with empresa(empresa_a.id):
        categoria = crear_categoria()
        juan = crear_entidad("Juan")
        rol = rol_de(juan, categoria_entidad_id=categoria.pk)

    assert rol.categoria_entidad_id == categoria.pk


def test_un_tipo_de_rol_de_otra_lista_se_rechaza(
    empresa_a, crear_entidad, catalogo_entidades
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

        with pytest.raises(ValidationError, match="Se esperaba un tipo de rol"):
            entidades.crear_rol(
                entidad_id=juan.pk,
                tipo_rol_id=catalogo_entidades["doc_ci"].pk,  # ← lista 6
                estado_id=catalogo_entidades["estado_activo"].pk,
            )


def test_el_limite_de_credito_no_puede_ser_negativo(
    empresa_a, crear_entidad, rol_de
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

        with pytest.raises(ValidationError, match="negativo"):
            rol_de(juan, limite_credito=-1)


def test_datos_rol_arranca_como_un_diccionario_vacio(
    empresa_a, crear_entidad, rol_de
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        rol = rol_de(juan)

    assert rol.datos_rol == {}
