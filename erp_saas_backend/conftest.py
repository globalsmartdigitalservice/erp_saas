"""
Fixtures compartidas por todos los tests.

Armar una `Empresa` no es trivial: necesita tres tipologías
(tipo, rubro, estado), un idioma y una moneda, y la moneda a su vez
necesita otra tipología. Por eso el catálogo mínimo se arma una sola
vez acá y no en cada test.

Todo el armado va dentro de `sin_filtro_de_empresa()`: es exactamente
el caso para el que existe esa puerta de salida — código que cruza
empresas a propósito.
"""

import pytest

from core.tenancy import sin_filtro_de_empresa


@pytest.fixture
def catalogo(db):
    """
    El catálogo de sistema mínimo: las tipologías globales, un idioma
    y una moneda. Todo con `empresa=None` (= del sistema).
    """
    from comun.idiomas.models import Idioma
    from comun.monedas.models import Moneda
    from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
    from comun.tipologias.models import Tipologia

    with sin_filtro_de_empresa():
        contador = {"n": 0}

        def tipologia(agrupador, nombre, empresa=None):
            # El índice arranca en 1: el 0 es la CABECERA de la lista
            # y ninguna consulta de valores la devuelve, así que
            # una tipología de prueba con 0 no saldría en ningún combo.
            contador["n"] += 1
            return Tipologia.objects.create(
                empresa=empresa,
                agrupador=agrupador,
                nombre=nombre,
                indice=contador["n"],
            )

        # La fila de alta/baja compartida por todos los catálogos.
        # Por la CONSTANTE y no a mano: `empresa_moneda.py` busca esta
        # fila por nombre, así que un literal desincronizado hace fallar
        # el service, no este archivo.
        estado_activo = tipologia(
            AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
        )

        datos = {
            "tipo_empresa": tipologia(AGRUPADOR.TIPO_EMPRESA, "Sociedad anónima"),
            "rubro": tipologia(AGRUPADOR.RUBRO, "Comercio"),
            "estado_empresa": tipologia(AGRUPADOR.ESTADO_EMPRESA, "ACTIVA"),
            "estado_activo": estado_activo,
            "idioma": Idioma.objects.create(codigo="es", nombre="Español"),
            "moneda": Moneda.objects.create(
                descripcion="Boliviano",
                codigo="BOB",
                simbolo="Bs",
                estado=estado_activo,
            ),
            "tipologia": tipologia,
        }

    return datos


@pytest.fixture
def crear_empresa(catalogo):
    """
    Fábrica de empresas: `crear_empresa("Acme")`.

    Con `padre` crea una SUCURSAL: `crear_empresa("El Alto", padre=matriz)`.
    Va por el modelo y no por el service a propósito —los invariantes del
    alta se prueban en `comun/empresas`, no acá—, así que comparte el NIT
    con la matriz como en la vida real.
    """
    from comun.empresas.models import Empresa

    contador = {"n": 0}

    def _crear(razon_social, padre=None):
        contador["n"] += 1
        with sin_filtro_de_empresa():
            empresa = Empresa.objects.create(
                empresa_padre=padre,
                ident_tributaria=f"NIT-{contador['n']:04d}",
                razon_social=razon_social,
                tipo_empresa=catalogo["tipo_empresa"],
                rubro=catalogo["rubro"],
                estado=catalogo["estado_empresa"],
                idioma_default=catalogo["idioma"],
            )

        # La moneda base ya no es una columna de `empresa`: es una fila
        # en `empresa_moneda`. Se crea acá para que la empresa de
        # prueba quede completa, igual que la crea el service del alta.
        from comun.empresas.models import EmpresaMoneda

        with sin_filtro_de_empresa():
            EmpresaMoneda.objects.create(
                empresa=empresa,
                moneda=catalogo["moneda"],
                es_moneda_oficial=True,
                estado=catalogo["estado_activo"],
            )

        return empresa

    return _crear


@pytest.fixture
def empresa_a(crear_empresa):
    return crear_empresa("Empresa A")


@pytest.fixture
def empresa_b(crear_empresa):
    """La empresa vecina. Existe para comprobar que A nunca la ve."""
    return crear_empresa("Empresa B")


@pytest.fixture
def sucursal_a(crear_empresa, empresa_a):
    """
    Una sucursal de A. Es OTRA empresa, con su propio id.

    La configuración baja de la matriz (tipologías); los datos no. Esa
    diferencia es lo que prueban los tests de herencia.
    """
    return crear_empresa("Sucursal de A", padre=empresa_a)


@pytest.fixture
def usuario_proveedor(db):
    """Una cuenta sin cliente: `matriz` vacía.

    Va por `objects.create()` porque `create_user()` exige el cliente a
    propósito. No es superusuario: así se comprueba que `@solo_proveedor`
    pasa por la matriz vacía y no por `is_superuser`.
    """
    from comun.usuarios.models import Usuario

    return Usuario.objects.create(username="proveedor", email="proveedor@erp.test")


@pytest.fixture
def contexto_proveedor(usuario_proveedor):
    from core.tests.contexto_graphql import Contexto

    return Contexto(usuario_proveedor)


@pytest.fixture
def contexto_superusuario(db):
    """Una sesión que pasa cualquier guard: el superusuario corta antes del permiso.

    Es para los tests que prueban el RESOLVER y no la autorización. Esa tiene
    sus propios tests en `dominios/seguridad`, y armar acá un rol con permisos
    haría que cada test de otra cosa dependa del módulo 12.
    """
    from comun.usuarios.models import Usuario
    from core.tests.contexto_graphql import Contexto

    return Contexto(
        Usuario.objects.create(
            username="superusuario", email="super@erp.test", is_superuser=True
        )
    )


@pytest.fixture
def contexto_con_sesion(contexto_proveedor):
    """Cualquier sesión abierta, para los guards que solo piden estar dentro.

    Reusa la cuenta del proveedor porque una de cliente necesita una empresa
    ya creada, y acá no se prueba de quién es la cuenta sino que haya sesión.
    """
    return contexto_proveedor
