import pytest
from django.core.exceptions import ValidationError
from django.db import transaction

from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa
from servicios.numeracion import api as numeracion

pytestmark = pytest.mark.django_db


def test_los_numeros_salen_del_uno_y_en_orden(empresa_a, serie_facturas):
    with empresa(empresa_a.id):
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 1
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 2
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 3


def test_numero_actual_no_consume(empresa_a, serie_facturas):
    with empresa(empresa_a.id):
        numeracion.siguiente_numero(serie_facturas.pk, 2026)

        assert numeracion.numero_actual(serie_facturas.pk, 2026) == 1
        assert numeracion.numero_actual(serie_facturas.pk, 2026) == 1

        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 2


def test_numero_actual_de_una_gestion_sin_uso_es_cero(empresa_a, serie_facturas):
    with empresa(empresa_a.id):
        assert numeracion.numero_actual(serie_facturas.pk, 2030) == 0


def test_formatear_arma_el_numero_impreso(empresa_a, serie_facturas):
    with empresa(empresa_a.id):
        assert numeracion.formatear(serie_facturas.pk, 123) == "FAC-000123"


def test_el_rollback_devuelve_el_numero(empresa_a, serie_facturas):
    with empresa(empresa_a.id):
        primero = numeracion.siguiente_numero(serie_facturas.pk, 2026)
        assert primero == 1

        with pytest.raises(RuntimeError):
            with transaction.atomic():
                perdido = numeracion.siguiente_numero(serie_facturas.pk, 2026)
                assert perdido == 2
                raise RuntimeError("la venta falló después de tomar el número")

        
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 2


def test_dos_gestiones_no_comparten_contador(empresa_a, serie_facturas):
    with empresa(empresa_a.id):
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 1
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 2

        assert numeracion.siguiente_numero(serie_facturas.pk, 2027) == 1

  
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 3


def test_dos_series_no_comparten_contador(
    empresa_a, serie_facturas, serie_recibos
):
    with empresa(empresa_a.id):
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 1
        assert numeracion.siguiente_numero(serie_facturas.pk, 2026) == 2

        assert numeracion.siguiente_numero(serie_recibos.pk, 2026) == 1


def test_no_se_puede_numerar_una_serie_de_otra_empresa(
    empresa_a, empresa_b, serie_facturas
):
    with empresa(empresa_b.id):
        with pytest.raises(ValidationError, match="No existe la serie"):
            numeracion.siguiente_numero(serie_facturas.pk, 2026)


def test_el_correlativo_deriva_su_empresa_de_la_serie(
    empresa_a, empresa_b, serie_facturas
):
    with empresa(empresa_a.id):
        numeracion.siguiente_numero(serie_facturas.pk, 2026)
        assert len(numeracion.listar_correlativos_de(serie_facturas.pk)) == 1

    with empresa(empresa_b.id):
        assert numeracion.listar_correlativos_de(serie_facturas.pk) == []


def test_una_gestion_que_no_es_un_ano_se_rechaza(empresa_a, serie_facturas):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="año válido"):
            numeracion.siguiente_numero(serie_facturas.pk, 26)


def test_no_se_puede_cambiar_el_prefijo_de_una_serie_que_ya_numero(
    empresa_a, serie_facturas
):
    with empresa(empresa_a.id):
        numeracion.actualizar_serie(serie_facturas.pk, prefijo="FACT")

        numeracion.siguiente_numero(serie_facturas.pk, 2026)

        with pytest.raises(ValidationError, match="ya emitió documentos"):
            numeracion.actualizar_serie(serie_facturas.pk, prefijo="OTRO")


def test_una_serie_repetida_se_rechaza(
    empresa_a, catalogo_numeracion, serie_facturas
):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Ya hay una serie"):
            numeracion.crear_serie(
                tipo_documento_id=catalogo_numeracion["factura"].pk,
                estado_id=catalogo_numeracion["estado_activo"].pk,
                prefijo="FAC",
            )


def test_un_tipo_de_documento_de_otra_empresa_se_rechaza(
    empresa_a, empresa_b, catalogo_numeracion
):
    with empresa(empresa_b.id):
        with pytest.raises(ValidationError, match="No existe el tipo de documento"):
            numeracion.crear_serie(
                tipo_documento_id=catalogo_numeracion["factura"].pk,
                estado_id=catalogo_numeracion["estado_activo"].pk,
                prefijo="X",
            )


def test_un_estado_de_otra_lista_se_rechaza(empresa_a, catalogo_numeracion):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Se esperaba un estado del registro"):
            numeracion.crear_serie(
                tipo_documento_id=catalogo_numeracion["factura"].pk,
                estado_id=catalogo_numeracion["tipologia"](
                    AGRUPADOR.RUBRO, "UN RUBRO"
                ).pk,
                prefijo="Z",
            )
