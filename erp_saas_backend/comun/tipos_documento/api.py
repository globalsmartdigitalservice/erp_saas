"""
Superficie pública de `tipos_documento`. El resto de la app es privado.

    from comun.tipos_documento import api as tipos_documento

 VIVE EN `comun/` (CAPA 2) Y NO EN SU MÓDULO DEL MODELO DE DATOS (05.3.1,
CAPA 4) porque la referencia `servicios/numeracion/` (CAPA 3): una FK de
CAPA 3 a CAPA 4 sería una dependencia hacia arriba. Es el mismo
movimiento que ya se hizo con `Entidad` y con `Licencia`.
"""

from comun.tipos_documento.models import TipoDocumentoComercial
from comun.tipos_documento.repository import tipo_documento_comercial as _repo
from comun.tipos_documento.services import tipo_documento_comercial as _svc


def obtener(tipo_id: int) -> TipoDocumentoComercial | None:
    return _repo.obtener(tipo_id)


def obtener_varios(tipo_ids) -> dict[int, TipoDocumentoComercial]:
    return _repo.obtener_varios(tipo_ids)


def listar() -> list[TipoDocumentoComercial]:
    return _repo.listar()


def crear(**campos) -> TipoDocumentoComercial:
    return _svc.crear(**campos)


def actualizar(tipo_id: int, **campos) -> TipoDocumentoComercial:
    return _svc.actualizar(tipo_id, **campos)


def desactivar(tipo_id: int) -> TipoDocumentoComercial:
    return _svc.desactivar(tipo_id)
