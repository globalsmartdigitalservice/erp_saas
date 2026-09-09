import pytest

from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa


@pytest.fixture
def catalogo_numeracion(catalogo, empresa_a):
    """Los tipos de documento de la empresa A, más lo que ya traía el catálogo."""
    from comun.tipos_documento import api as tipos_documento

    with empresa(empresa_a.id):
        factura = tipos_documento.crear(
            codigo="FAC",
            nombre="FACTURA",
            estado_id=catalogo["estado_activo"].pk,
            afecta_stock=True,
            genera_ingreso=True,
            es_venta=True,
        )
        recibo = tipos_documento.crear(
            codigo="REC",
            nombre="RECIBO",
            estado_id=catalogo["estado_activo"].pk,
            genera_ingreso=True,
        )

    return {**catalogo, "factura": factura, "recibo": recibo}


@pytest.fixture
def serie_facturas(catalogo_numeracion, empresa_a):
    from servicios.numeracion import api as numeracion

    with empresa(empresa_a.id):
        return numeracion.crear_serie(
            tipo_documento_id=catalogo_numeracion["factura"].pk,
            estado_id=catalogo_numeracion["estado_activo"].pk,
            prefijo="FAC",
        )


@pytest.fixture
def serie_recibos(catalogo_numeracion, empresa_a):
    from servicios.numeracion import api as numeracion

    with empresa(empresa_a.id):
        return numeracion.crear_serie(
            tipo_documento_id=catalogo_numeracion["recibo"].pk,
            estado_id=catalogo_numeracion["estado_activo"].pk,
            prefijo="REC",
        )
