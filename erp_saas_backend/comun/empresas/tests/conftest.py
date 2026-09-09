import pytest

from comun.empresas.services.empresa import (
    NOMBRE_ESTADO_INACTIVA,
    NOMBRE_TIPO_MATRIZ,
)
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ESTADO_ACTIVO,
    NOMBRE_ESTADO_BAJA,
)
from comun.tipologias.models import Tipologia
from core.tenancy import sin_filtro_de_empresa


@pytest.fixture
def tipologia():
    """Fábrica: `tipologia(AGRUPADOR.RUBRO, "Comercio")`.

     El `indice` arranca en 1 y nunca es 0: el 0 es la CABECERA, la
    fila que guarda el NOMBRE de la lista, y ninguna consulta de valores
    la devuelve. Una tipología de prueba con índice 0 no
    aparecería en ningún combo y el test fallaría por el motivo
    equivocado.
    """

    contador = {"n": 0}

    def _crear(agrupador, nombre):
        contador["n"] += 1
        with sin_filtro_de_empresa():
            return Tipologia.objects.create(
                empresa=None,
                agrupador=agrupador,
                nombre=nombre,
                indice=contador["n"],
            )

    return _crear


@pytest.fixture
def catalogo_empresas(db, tipologia):
    """
    El catálogo mínimo para dar de alta una empresa.

    Los nombres NO son decorativos: `services/empresa.py` busca la matriz
    y la baja POR NOMBRE, porque son los que la semilla garantiza
    (las semillas). Por eso salen de sus constantes y no escritos a mano:
    así no hay forma de que este archivo y el service se desincronicen.

    `Empresa` conserva su propia lista de estados —"Suspendida" no es ni
    alta ni baja—, así que "ACTIVA"/"INACTIVA" NO son la fila
    compartida.
    """
    from comun.geografia import api as geografia
    from comun.idiomas import api as idiomas
    from comun.monedas import api as monedas


    estado_activo = tipologia(AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO)

    return {
        "tipo_matriz": tipologia(AGRUPADOR.TIPO_EMPRESA, NOMBRE_TIPO_MATRIZ),
        "tipo_sucursal": tipologia(AGRUPADOR.TIPO_EMPRESA, "SUCURSAL"),
        "rubro": tipologia(AGRUPADOR.RUBRO, "Comercio"),
        "activa": tipologia(AGRUPADOR.ESTADO_EMPRESA, "ACTIVA"),
        "inactiva": tipologia(
            AGRUPADOR.ESTADO_EMPRESA, NOMBRE_ESTADO_INACTIVA
        ),
        "idioma": idiomas.crear_idioma(codigo="es", nombre="Español"),
        "moneda": monedas.crear_moneda(
            descripcion="Boliviano",
            codigo="BOB",
            estado_id=estado_activo.pk,
        ),
        "bolivia": geografia.crear_pais(
            cod_pais="BO", nombre="Bolivia", codigo_iso="BOL", estado_id=estado_activo.pk
        ),
        "peru": geografia.crear_pais(
            cod_pais="PE", nombre="Perú", codigo_iso="PER", estado_id=estado_activo.pk
        ),
    
        "estado_activo": estado_activo,
    }


@pytest.fixture
def datos_base(catalogo_empresas):
    """Los campos obligatorios de un alta, para no repetirlos en cada test."""
    c = catalogo_empresas
    return {
        "tipo_empresa_id": c["tipo_matriz"].pk,
        "rubro_id": c["rubro"].pk,
        "estado_id": c["activa"].pk,
        "idioma_default_id": c["idioma"].pk,
        "moneda_oficial_id": c["moneda"].pk,
        "pais_id": c["bolivia"].pk,
    }


@pytest.fixture
def matriz(db, datos_base):
    from comun.empresas import api as empresas

    return empresas.crear_empresa(
        ident_tributaria="1234567",
        razon_social="Ferretería El Tornillo S.A.",
        nombre_comercial="El Tornillo",
        **datos_base,
    )


@pytest.fixture
def crear_sucursal_de(db, datos_base, catalogo_empresas):
    """
    Fábrica de sucursales colgadas de cualquier empresa, no solo de la
    matriz. Sirve para armar cadenas de más de dos niveles.
    """
    from comun.empresas import api as empresas

    def _crear(padre, razon_social):
        datos = {**datos_base, "tipo_empresa_id": catalogo_empresas["tipo_sucursal"].pk}
        return empresas.crear_empresa(
            ident_tributaria=padre.ident_tributaria,
            razon_social=razon_social,
            empresa_padre_id=padre.pk,
            **datos,
        )

    return _crear


@pytest.fixture
def otra_empresa(db, datos_base):
    """La empresa de OTRO cliente: existe para comprobar que nunca entra."""
    from comun.empresas import api as empresas

    return empresas.crear_empresa(
        ident_tributaria="9876543",
        razon_social="Farmacia San Juan S.R.L.",
        nombre_comercial="San Juan",
        **datos_base,
    )


@pytest.fixture
def sucursal(db, matriz, datos_base, catalogo_empresas):
    """
    Una sucursal de la matriz, **con el mismo NIT**: así es en Bolivia.
    """
    from comun.empresas import api as empresas

    datos = {**datos_base, "tipo_empresa_id": catalogo_empresas["tipo_sucursal"].pk}
    return empresas.crear_empresa(
        ident_tributaria="1234567",
        razon_social="Ferretería El Tornillo S.A. - El Alto",
        empresa_padre_id=matriz.pk,
        **datos,
    )
