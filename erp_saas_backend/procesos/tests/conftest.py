"""Lo que los procesos de alta necesitan y el catálogo compartido no trae.

El `catalogo` de la raíz arma una empresa genérica; estos procesos buscan filas
concretas POR NOMBRE —"CASA MATRIZ", "SUCURSAL"— y además necesitan un país y
al menos un permiso en el catálogo.
"""

import pytest

from comun.empresas.services.empresa import (
    NOMBRE_TIPO_MATRIZ,
    NOMBRE_TIPO_SUCURSAL,
)
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ACCESO_BLOQUEADO,
    NOMBRE_ACCESO_EXITO,
    NOMBRE_ACCESO_FALLO,
)


@pytest.fixture
def catalogo_de_altas(catalogo):
    from django.contrib.auth.models import Permission

    from comun.geografia import api as geografia
    from core.tenancy import sin_filtro_de_empresa
    from dominios.seguridad.permisos import content_type_del_ancla

    tipologia = catalogo["tipologia"]
    with sin_filtro_de_empresa():
        tipologia(AGRUPADOR.TIPO_EMPRESA, NOMBRE_TIPO_MATRIZ)
        tipologia(AGRUPADOR.TIPO_EMPRESA, NOMBRE_TIPO_SUCURSAL)
        for nombre in (
            NOMBRE_ACCESO_EXITO,
            NOMBRE_ACCESO_BLOQUEADO,
            NOMBRE_ACCESO_FALLO,
        ):
            tipologia(AGRUPADOR.RESULTADO_ACCESO, nombre)

    bolivia = geografia.crear_pais(
        cod_pais="BO",
        nombre="Bolivia",
        codigo_iso="BOL",
        estado_id=catalogo["estado_activo"].pk,
    )
    Permission.objects.create(
        content_type=content_type_del_ancla(),
        codename="segu_roles_crear_rol",
        name="Crear rol",
    )

    return {**catalogo, "bolivia": bolivia}


@pytest.fixture
def datos_del_cliente(catalogo_de_altas):
    from procesos import alta_de_cliente

    return alta_de_cliente.DatosDelCliente(
        ident_tributaria="1234567",
        razon_social="Farmacia Vida",
        rubro_id=catalogo_de_altas["rubro"].pk,
        pais_id=catalogo_de_altas["bolivia"].pk,
        moneda_oficial_id=catalogo_de_altas["moneda"].pk,
        idioma_default_id=catalogo_de_altas["idioma"].pk,
    )


@pytest.fixture
def datos_de_carla():
    from procesos import alta_de_cliente

    return alta_de_cliente.DatosDelAdministrador(
        username="carla.mamani",
        email="carla@vida.bo",
        first_name="Carla",
        last_name="Mamani",
    )


@pytest.fixture
def farmacia_vida(datos_del_cliente, datos_de_carla):
    """Un cliente ya dado de alta, con Carla adentro."""
    from procesos import alta_de_cliente

    return alta_de_cliente.dar_de_alta(
        cliente=datos_del_cliente, administrador=datos_de_carla
    )
