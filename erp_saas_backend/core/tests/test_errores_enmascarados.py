import logging

import pytest
import strawberry
from graphql import GraphQLError

from core.graphql import EnmascararErrores, SchemaDelErp

SECRETO = "duplicate key value violates unique constraint ent_entidad_documento_unico"
MENSAJE_DE_DOMINIO = "Ya hay una entidad con el documento '9846372' en esta empresa."


@strawberry.type
class Consulta:
    @strawberry.field
    def bien(self) -> str:
        return "ok"

    @strawberry.field
    def error_de_dominio(self) -> str:
        # Lo mismo que hace `_traducir` en cada módulo.
        raise GraphQLError(MENSAJE_DE_DOMINIO)

    @strawberry.field
    def error_inesperado(self) -> str:
        # Un bug: se escapó una excepción con texto técnico adentro.
        raise ValueError(SECRETO)


schema = SchemaDelErp(query=Consulta, extensions=[EnmascararErrores()])


@pytest.fixture
def log_del_erp(caplog):
    """
    Lo que escribe `erp.graphql`.

     NO ALCANZA CON `caplog` SOLO, Y CUESTA UNA HORA DESCUBRIRLO: el
    logger `erp` está declarado con `propagate: False` en el settings —a
    propósito, para que sus líneas no salgan dos veces—, y pytest engancha
    su handler en la RAÍZ. Con la propagación cortada, a la raíz no llega
    nada y `caplog.text` queda vacío aunque el log funcione perfecto.
    Por eso el handler se cuelga directo del logger.
    """
    logger = logging.getLogger("erp.graphql")
    logger.addHandler(caplog.handler)
    yield caplog
    logger.removeHandler(caplog.handler)


def test_el_mensaje_de_dominio_llega_intacto():
    resultado = schema.execute_sync("{ errorDeDominio }")

    assert resultado.errors is not None
    assert resultado.errors[0].message == MENSAJE_DE_DOMINIO


def test_el_error_inesperado_no_llega_al_cliente():
    resultado = schema.execute_sync("{ errorInesperado }")

    mensaje = resultado.errors[0].message

    assert SECRETO not in mensaje
    assert "constraint" not in mensaje
    assert "ValueError" not in mensaje
    assert "referencia" in mensaje


def test_el_error_inesperado_trae_una_referencia_para_reportarlo():
    resultado = schema.execute_sync("{ errorInesperado }")

    referencia = resultado.errors[0].extensions["referencia"]

    assert referencia

    assert referencia in resultado.errors[0].message


def test_la_referencia_del_log_es_la_que_ve_el_usuario(log_del_erp):
    resultado = schema.execute_sync("{ errorInesperado }")

    referencia = resultado.errors[0].extensions["referencia"]

    assert referencia in log_del_erp.text
   
    assert SECRETO in log_del_erp.text


def test_un_rechazo_esperado_no_deja_traceback_en_el_log(log_del_erp):
    schema.execute_sync("{ errorDeDominio }")

    assert MENSAJE_DE_DOMINIO in log_del_erp.text
    assert "Traceback" not in log_del_erp.text
    assert [r for r in log_del_erp.records if r.levelno >= logging.ERROR] == []


def test_una_consulta_mal_escrita_conserva_su_mensaje():
    resultado = schema.execute_sync("{ campoQueNoExiste }")

    assert "campoQueNoExiste" in resultado.errors[0].message


def test_lo_que_sale_bien_sigue_saliendo_bien():
    resultado = schema.execute_sync("{ bien }")

    assert resultado.errors is None
    assert resultado.data == {"bien": "ok"}


def test_el_schema_del_erp_es_el_que_esta_puesto_en_config():
    from config.schema import schema as schema_real

    assert isinstance(schema_real, SchemaDelErp)
    assert any(
        isinstance(extension, EnmascararErrores)
        for extension in schema_real.extensions
    )
