"""Los inputs de las mutations."""

import decimal

import strawberry


@strawberry.input
class CrearEmpresaInput:
    ident_tributaria: str
    razon_social: str
    tipo_empresa_id: strawberry.ID
    rubro_id: strawberry.ID
    estado_id: strawberry.ID
    idioma_default_id: strawberry.ID

    moneda_oficial_id: strawberry.ID
    pais_id: strawberry.ID
    nombre_comercial: str = ""
    empresa_padre_id: strawberry.ID | None = None
    ubicacion_geografica_id: strawberry.ID | None = None
  


@strawberry.input
class ActualizarEmpresaInput:
    ident_tributaria: str | None = None
    razon_social: str | None = None
    nombre_comercial: str | None = None
    tipo_empresa_id: strawberry.ID | None = None
    rubro_id: strawberry.ID | None = None
    estado_id: strawberry.ID | None = None
    idioma_default_id: strawberry.ID | None = None

    empresa_padre_id: strawberry.ID | None = None
    ubicacion_geografica_id: strawberry.ID | None = None


@strawberry.input
class AgregarPaisInput:
    empresa_id: strawberry.ID
    pais_id: strawberry.ID
    ubicacion_geografica_id: strawberry.ID | None = None
    direccion: str = ""
    telefono: str = ""
    email: str = ""
    sitio_web: str = ""
    logo: str = ""
    latitud: decimal.Decimal | None = None
    longitud: decimal.Decimal | None = None


@strawberry.input
class ActualizarPaisDeEmpresaInput:
    """Los datos de contacto de la ficha, y nada más.

    No lleva `empresaId` —sale de la sesión— ni `paisId`: cambiar el país es
    borrar la ficha de uno y crear la de otro, y eso se hace explícito.
    Un campo en nulo significa "no lo toques"."""

    ubicacion_geografica_id: strawberry.ID | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    sitio_web: str | None = None
    logo: str | None = None
    latitud: decimal.Decimal | None = None
    longitud: decimal.Decimal | None = None
