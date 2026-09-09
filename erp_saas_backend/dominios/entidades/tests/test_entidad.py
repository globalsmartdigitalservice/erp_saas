import pytest
from django.core.exceptions import ValidationError

from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from core.tenancy import empresa
from dominios.entidades import api as entidades

pytestmark = pytest.mark.django_db


def test_crear_una_entidad_le_pone_la_empresa_del_contexto(
    empresa_a, crear_entidad
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan", documento="1234567")

    assert juan.empresa_id == empresa_a.id
    assert juan.documento == "1234567"


def test_la_entidad_de_otra_empresa_no_existe(empresa_a, empresa_b, crear_entidad):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")

    with empresa(empresa_b.id):
        assert entidades.obtener_entidad(juan.pk) is None
        assert entidades.listar_entidades().items == []


def test_desactivar_es_soft_delete(empresa_a, crear_entidad, catalogo_entidades):
    baja = catalogo_entidades["tipologia"](
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )

    with empresa(empresa_a.id):
        juan = crear_entidad("Juan")
        dada_de_baja = entidades.desactivar_entidad(juan.pk)

        # Sigue estando: lo que cambia es el estado, no la existencia.
        assert entidades.obtener_entidad(juan.pk) is not None

    assert dada_de_baja.estado_id == baja.pk


def test_el_mismo_documento_se_repite_entre_empresas(
    empresa_a, empresa_b, crear_entidad
):
    with empresa(empresa_a.id):
        crear_entidad("Ferretería El Tornillo", documento="1234567")

    with empresa(empresa_b.id):
        otra = crear_entidad("Ferretería El Tornillo", documento="1234567")

    assert otra.pk is not None


def test_el_mismo_documento_no_se_repite_dentro_de_la_empresa(
    empresa_a, crear_entidad
):
    with empresa(empresa_a.id):
        crear_entidad("Juan", documento="1234567")

        with pytest.raises(ValidationError, match="1234567"):
            crear_entidad("Juan otra vez", documento="1234567")


def test_varias_entidades_pueden_no_tener_documento(empresa_a, crear_entidad):
    with empresa(empresa_a.id):
        crear_entidad("Sin papeles 1")
        crear_entidad("Sin papeles 2")

        assert entidades.listar_entidades().total == 2


def test_el_documento_se_normaliza_antes_de_comparar(empresa_a, crear_entidad):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan", documento="  1234567  ")
        assert juan.documento == "1234567"

        with pytest.raises(ValidationError):
            crear_entidad("Duplicado", documento="1234567")


def test_actualizar_a_un_documento_ya_usado_se_rechaza(empresa_a, crear_entidad):
    with empresa(empresa_a.id):
        crear_entidad("Juan", documento="111")
        pedro = crear_entidad("Pedro", documento="222")

        with pytest.raises(ValidationError, match="111"):
            entidades.actualizar_entidad(pedro.pk, documento="111")


def test_actualizar_dejandole_su_propio_documento_no_se_rechaza(
    empresa_a, crear_entidad
):
    with empresa(empresa_a.id):
        juan = crear_entidad("Juan", documento="111")
        actualizada = entidades.actualizar_entidad(
            juan.pk, nombre="Juan Pérez", documento="111"
        )

    assert actualizada.nombre == "Juan Pérez"


def test_un_tipo_de_entidad_de_otra_lista_se_rechaza(
    empresa_a, catalogo_entidades
):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Se esperaba un tipo de entidad"):
            entidades.crear_entidad(
                tipo_entidad_id=catalogo_entidades["doc_ci"].pk,  # ← lista 6
                nombre="Juan",
                tipo_documento_id=catalogo_entidades["doc_ci"].pk,
                estado_id=catalogo_entidades["estado_activo"].pk,
            )


def test_un_tipo_de_documento_de_otra_lista_se_rechaza(
    empresa_a, catalogo_entidades
):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Se esperaba un tipo de documento"):
            entidades.crear_entidad(
                tipo_entidad_id=catalogo_entidades["tipo_natural"].pk,
                nombre="Juan",
                tipo_documento_id=catalogo_entidades["rol_cliente"].pk,  # ← lista 7
                estado_id=catalogo_entidades["estado_activo"].pk,
            )


def test_un_estado_de_otra_lista_se_rechaza(empresa_a, catalogo_entidades):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Se esperaba un estado del registro"):
            entidades.crear_entidad(
                tipo_entidad_id=catalogo_entidades["tipo_natural"].pk,
                nombre="Juan",
                tipo_documento_id=catalogo_entidades["doc_ci"].pk,
                estado_id=catalogo_entidades["rubro"].pk,  # ← la lista de rubros
            )


def test_una_tipologia_de_otra_empresa_no_sirve(
    empresa_a, empresa_b, catalogo_entidades
):
    tipo_de_b = catalogo_entidades["tipologia"](
        AGRUPADOR.TIPO_ENTIDAD, "TIPO PRIVADO DE B", empresa=empresa_b
    )

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Se esperaba un tipo de entidad"):
            entidades.crear_entidad(
                tipo_entidad_id=tipo_de_b.pk,
                nombre="Juan",
                tipo_documento_id=catalogo_entidades["doc_ci"].pk,
                estado_id=catalogo_entidades["estado_activo"].pk,
            )
