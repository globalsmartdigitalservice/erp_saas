import pytest

from comun.tipologias.constantes import AGRUPADOR


@pytest.fixture
def catalogo_entidades(catalogo):
    """Las cuatro listas del módulo 04, más las que ya había."""
    tipologia = catalogo["tipologia"]

    return {
        **catalogo,
        "tipo_natural": tipologia(AGRUPADOR.TIPO_ENTIDAD, "PERSONA NATURAL"),
        "tipo_juridica": tipologia(AGRUPADOR.TIPO_ENTIDAD, "PERSONA JURÍDICA"),
        "doc_ci": tipologia(AGRUPADOR.TIPO_DOCUMENTO, "CÉDULA DE IDENTIDAD"),
        "doc_nit": tipologia(AGRUPADOR.TIPO_DOCUMENTO, "NIT"),
        "rol_cliente": tipologia(AGRUPADOR.TIPO_ROL, "CLIENTE"),
        "rol_proveedor": tipologia(AGRUPADOR.TIPO_ROL, "PROVEEDOR"),
        "dir_domicilio": tipologia(AGRUPADOR.TIPO_DIRECCION, "DOMICILIO"),
    }


@pytest.fixture
def crear_entidad(catalogo_entidades):
    """
    Fábrica: `crear_entidad("Juan")`, ya dentro del contexto de empresa.

    Va por el `api.py`, no por el modelo: así cada fixture ejercita los
    invariantes en vez de esquivarlos.
    """
    from dominios.entidades import api as entidades

    def _crear(nombre="Juan", documento="", **extra):
        campos = {
            "tipo_entidad_id": catalogo_entidades["tipo_natural"].pk,
            "nombre": nombre,
            "tipo_documento_id": catalogo_entidades["doc_ci"].pk,
            "documento": documento,
            "estado_id": catalogo_entidades["estado_activo"].pk,
        }
        campos.update(extra)
        return entidades.crear_entidad(**campos)

    return _crear


@pytest.fixture
def rol_de(catalogo_entidades):
    """
    Fábrica: `rol_de(entidad, "rol_cliente")`.

    Vive acá y no en `test_rol_entidad.py` porque también la usa
    `test_graphql.py`: una fixture declarada dentro de un módulo de tests
    no la ve ningún otro módulo.
    """
    from dominios.entidades import api as entidades

    def _crear(entidad, clave="rol_cliente", **extra):
        campos = {
            "entidad_id": entidad.pk,
            "tipo_rol_id": catalogo_entidades[clave].pk,
            "estado_id": catalogo_entidades["estado_activo"].pk,
        }
        campos.update(extra)
        return entidades.crear_rol(**campos)

    return _crear


@pytest.fixture
def crear_categoria(catalogo_entidades):
    """Fábrica: `crear_categoria("MAYORISTA")`, con su estado ya puesto."""
    from dominios.entidades import api as entidades

    def _crear(nombre="MAYORISTA", **extra):
        campos = {
            "nombre": nombre,
            "estado_id": catalogo_entidades["estado_activo"].pk,
        }
        campos.update(extra)
        return entidades.crear_categoria(**campos)

    return _crear


@pytest.fixture
def crear_contacto(catalogo_entidades):
    """Fábrica: `crear_contacto(entidad, "Ana")`."""
    from dominios.entidades import api as entidades

    def _crear(entidad, nombre="Ana", **extra):
        campos = {
            "entidad_id": entidad.pk,
            "nombre": nombre,
            "estado_id": catalogo_entidades["estado_activo"].pk,
        }
        campos.update(extra)
        return entidades.crear_contacto(**campos)

    return _crear
