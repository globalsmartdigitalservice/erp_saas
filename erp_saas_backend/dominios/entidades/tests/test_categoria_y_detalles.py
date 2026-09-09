import datetime

import pytest
from django.core.exceptions import ValidationError

from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from core.tenancy import empresa
from dominios.entidades import api as entidades

pytestmark = pytest.mark.django_db


def test_el_nombre_de_categoria_no_se_repite_dentro_de_la_empresa(
    empresa_a, crear_categoria
):
    with empresa(empresa_a.id):
        crear_categoria()

        with pytest.raises(ValidationError, match="MAYORISTA"):
            crear_categoria()


def test_el_nombre_de_categoria_si_se_repite_entre_empresas(
    empresa_a, empresa_b, crear_categoria
):
    with empresa(empresa_a.id):
        crear_categoria()

    with empresa(empresa_b.id):
        otra = crear_categoria()

    assert otra.pk is not None


def test_el_descuento_no_puede_ser_negativo(empresa_a, crear_categoria):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="negativo"):
            crear_categoria("RARA", descuento_categ_cliente=-5)


def test_el_descuento_no_tiene_tope(empresa_a, crear_categoria):
    with empresa(empresa_a.id):
        categoria = crear_categoria("LIQUIDACIÓN", descuento_categ_cliente=120)

    assert categoria.pk is not None


def test_no_se_le_puede_poner_una_direccion_a_la_entidad_de_otra_empresa(
    empresa_a, empresa_b, crear_entidad, catalogo_entidades
):
    with empresa(empresa_a.id):
        de_a = crear_entidad("Juan de A")

    with empresa(empresa_b.id):
        with pytest.raises(ValidationError, match="No existe la entidad"):
            entidades.crear_direccion(
                entidad_id=de_a.pk,
                tipo_id=catalogo_entidades["dir_domicilio"].pk,
                estado_id=catalogo_entidades["estado_activo"].pk,
                calle="Sucre",
            )


def test_la_direccion_de_otra_empresa_no_se_lista(
    empresa_a, empresa_b, crear_entidad, catalogo_entidades
):
    """Sin el aislamiento, esto devolvería las direcciones de TODOS los
    clientes: sin error, con datos, y pareciendo que funciona."""
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        entidades.crear_direccion(
            entidad_id=juan.pk,
            tipo_id=catalogo_entidades["dir_domicilio"].pk,
            estado_id=catalogo_entidades["estado_activo"].pk,
            calle="Sucre",
        )

    with empresa(empresa_b.id):
        assert entidades.listar_direcciones_de(juan.pk) == []


def test_un_tipo_de_direccion_de_otra_lista_se_rechaza(
    empresa_a, crear_entidad, catalogo_entidades
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

        with pytest.raises(ValidationError, match="Se esperaba un tipo de dirección"):
            entidades.crear_direccion(
                entidad_id=juan.pk,
                tipo_id=catalogo_entidades["rol_cliente"].pk,  # ← lista 7
                estado_id=catalogo_entidades["estado_activo"].pk,
            )


def test_una_ubicacion_geografica_inexistente_se_rechaza(
    empresa_a, crear_entidad, catalogo_entidades
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

        with pytest.raises(ValidationError, match="ubicación geográfica"):
            entidades.crear_direccion(
                entidad_id=juan.pk,
                tipo_id=catalogo_entidades["dir_domicilio"].pk,
                estado_id=catalogo_entidades["estado_activo"].pk,
                ubicacion_geografica_id=999999,
            )


def test_el_contacto_de_otra_empresa_no_se_lista(
    empresa_a, empresa_b, crear_entidad, crear_contacto
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        crear_contacto(juan, cargo="Compras")

    with empresa(empresa_b.id):
        assert entidades.listar_contactos_de(juan.pk) == []


def test_el_contacto_no_se_borra_se_da_de_baja(
    empresa_a, crear_entidad, crear_contacto, catalogo_entidades
):
    baja = catalogo_entidades["tipologia"](
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )

    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        contacto = crear_contacto(juan)

        entidades.desactivar_contacto(contacto.pk)

        de_nuevo = entidades.obtener_contacto(contacto.pk)
        assert de_nuevo is not None
        assert de_nuevo.estado_id == baja.pk


def test_la_encuesta_de_otra_empresa_no_se_lista(
    empresa_a, empresa_b, crear_entidad
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        entidades.registrar_encuesta(
            entidad_id=juan.pk, fecha=datetime.date(2026, 9, 2), puntaje=5
        )

    with empresa(empresa_b.id):
        assert entidades.listar_encuestas_de(juan.pk) == []


def test_la_encuesta_no_valida_el_rango_del_puntaje(empresa_a, crear_entidad):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        encuesta = entidades.registrar_encuesta(
            entidad_id=juan.pk, fecha=datetime.date(2026, 9, 2), puntaje=97
        )

    assert encuesta.puntaje == 97
