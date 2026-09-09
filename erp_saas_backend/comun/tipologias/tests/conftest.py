import pytest

from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa


@pytest.fixture
def rubro_del_sistema(catalogo):
    """
    Una fila del catálogo global: la ven todas las empresas.

    Se reutiliza la que ya arma el `catalogo` de la raíz en vez de crear
    otra: la constraint (empresa, agrupador, nombre) rechazaría un
    segundo "Comercio" del sistema.
    """
    return catalogo["rubro"]


@pytest.fixture
def permitir_ampliar(db):
    """
    Fábrica: `permitir_ampliar(empresa_a, AGRUPADOR.RUBRO)`.

    `crear()` exige permiso: sin fila en
    `empresa_agrupador`, la empresa no puede agregar valores a esa
    lista. Los tests que crean tipologías tienen que
    dárselo primero — igual que se lo daría el proveedor.
    """

    def _permitir(la_empresa, agrupador):
        from comun.tipologias import api as tipologias

        return tipologias.habilitar_agrupador(la_empresa.id, agrupador)

    return _permitir


@pytest.fixture
def rubro_de(db, permitir_ampliar):
    """
    Fábrica: `rubro_de(empresa_a, "Farmacia")`.

    Crea la tipología DENTRO del contexto de esa empresa, que es como la
    va a crear el service de verdad. Habilita el permiso de paso, porque
    lo que estos tests prueban es otra cosa.
    """

    def _crear(la_empresa, nombre):
        from comun.tipologias import api as tipologias

        permitir_ampliar(la_empresa, AGRUPADOR.RUBRO)  # idempotente
        with empresa(la_empresa.id):
            return tipologias.crear(agrupador=AGRUPADOR.RUBRO, nombre=nombre)

    return _crear
