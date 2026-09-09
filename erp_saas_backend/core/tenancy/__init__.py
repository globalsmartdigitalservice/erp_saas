"""
Aislamiento entre empresas (multi-tenant).

Uso normal:

    from core.tenancy import ModeloTenant

    class Venta(ModeloTenant):
        ...

Y para las tablas que cuelgan de otra y NO repiten `empresa_id`
(las ~79 de detalle):

    from core.tenancy import ModeloTenantDerivado

    class DetalleVenta(ModeloTenantDerivado):
        RUTA_A_EMPRESA = "venta"
"""

from .contexto import (
    SinEmpresaEnContexto,
    empresa,
    empresa_actual,
    establecer_empresa,
    filtro_desactivado,
    hay_empresa,
    restaurar_empresa,
    sin_filtro_de_empresa,
)
from .managers import TenantDerivadoManager, TenantManager, TenantQuerySet
from .modelos import ModeloTenant, ModeloTenantDerivado, PadreDeOtraEmpresa

__all__ = [
    "ModeloTenant",
    "ModeloTenantDerivado",
    "PadreDeOtraEmpresa",
    "TenantManager",
    "TenantDerivadoManager",
    "TenantQuerySet",
    "SinEmpresaEnContexto",
    "empresa",
    "empresa_actual",
    "establecer_empresa",
    "filtro_desactivado",
    "restaurar_empresa",
    "hay_empresa",
    "sin_filtro_de_empresa",
]
