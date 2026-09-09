"""Los tipos que ve el frontend. Sin lógica: solo forma."""

import decimal

import strawberry

from comun.empresas.models import Empresa, EmpresaMoneda, EmpresaPais
from comun.tipologias.graphql.types import TipologiaType


@strawberry.type(name="Empresa")
class EmpresaType:
    id: strawberry.ID
    ident_tributaria: str
    razon_social: str
    nombre_comercial: str
    es_matriz: bool
    empresa_padre_id: strawberry.ID | None

    # Las tres se RECIBEN ya resueltas, por lote.
    tipo_empresa: TipologiaType | None
    rubro: TipologiaType | None
    estado: TipologiaType | None

    @classmethod
    def desde_modelo(
        cls,
        empresa: Empresa,
        tipo_empresa: TipologiaType | None = None,
        rubro: TipologiaType | None = None,
        estado: TipologiaType | None = None,
    ) -> "EmpresaType":
        padre = empresa.empresa_padre_id
        return cls(
            id=strawberry.ID(str(empresa.pk)),
            ident_tributaria=empresa.ident_tributaria,
            razon_social=empresa.razon_social,
            nombre_comercial=empresa.nombre_comercial,
            es_matriz=empresa.es_matriz,
            empresa_padre_id=strawberry.ID(str(padre)) if padre else None,
            tipo_empresa=tipo_empresa,
            rubro=rubro,
            estado=estado,
        )


@strawberry.type(name="EmpresaPais")
class EmpresaPaisType:
    id: strawberry.ID
    empresa_id: strawberry.ID
    pais_id: strawberry.ID
    ubicacion_geografica_id: strawberry.ID | None
    direccion: str
    telefono: str
    email: str
    sitio_web: str
    logo: str
    latitud: decimal.Decimal | None
    longitud: decimal.Decimal | None

    @classmethod
    def desde_modelo(cls, fila: EmpresaPais) -> "EmpresaPaisType":
        ubicacion = fila.ubicacion_geografica_id
        return cls(
            id=strawberry.ID(str(fila.pk)),
            empresa_id=strawberry.ID(str(fila.empresa_id)),
            pais_id=strawberry.ID(str(fila.pais_id)),
            ubicacion_geografica_id=(
                strawberry.ID(str(ubicacion)) if ubicacion else None
            ),
            direccion=fila.direccion,
            telefono=fila.telefono,
            email=fila.email,
            sitio_web=fila.sitio_web,
            logo=fila.logo,
            latitud=fila.latitud,
            longitud=fila.longitud,
        )


@strawberry.type(name="EmpresaMoneda")
class EmpresaMonedaType:
    """
    Una moneda habilitada para una empresa.

    `esMonedaOficial` vive acá y NO en `Moneda`: es la base de
    conversión de ESA empresa. En el catálogo esa marca no significaba
    nada — el boliviano no es "oficial" en sí mismo.
    """

    id: strawberry.ID
    empresa_id: strawberry.ID
    moneda_id: strawberry.ID
    es_moneda_oficial: bool
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, fila: EmpresaMoneda) -> "EmpresaMonedaType":
        return cls(
            id=strawberry.ID(str(fila.pk)),
            empresa_id=strawberry.ID(str(fila.empresa_id)),
            moneda_id=strawberry.ID(str(fila.moneda_id)),
            es_moneda_oficial=fila.es_moneda_oficial,
            estado_id=strawberry.ID(str(fila.estado_id)),
        )
