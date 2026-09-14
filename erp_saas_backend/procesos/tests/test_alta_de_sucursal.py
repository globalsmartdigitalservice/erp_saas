import dataclasses

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from comun.empresas.services.empresa import NOMBRE_TIPO_SUCURSAL
from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa
from dominios.seguridad import api as seguridad
from procesos import alta_de_sucursal

pytestmark = pytest.mark.django_db

Usuario = get_user_model()


@pytest.fixture
def tipo_sucursal(catalogo_de_altas):
    return tipologias.obtener_del_sistema(
        AGRUPADOR.TIPO_EMPRESA, NOMBRE_TIPO_SUCURSAL
    )


@pytest.fixture
def datos_de_norte(farmacia_vida, tipo_sucursal):
    return alta_de_sucursal.DatosDeLaSucursal(
        padre_id=farmacia_vida.empresa.pk,
        razon_social="Farmacia Vida - Norte",
        tipo_empresa_id=tipo_sucursal.pk,
        encargado_username=farmacia_vida.administrador.username,
    )


def test_la_sucursal_nace_con_su_encargado_adentro(farmacia_vida, datos_de_norte):
    """El mismo invariante que el alta de cliente, una escala más abajo: si
    naciera vacía sería imposible poblarla, porque para afiliar en Norte hay
    que estar parado en Norte y nadie tendría membresía."""
    norte = alta_de_sucursal.dar_de_alta(datos_de_norte)

    assert norte.empresa.empresa_padre_id == farmacia_vida.empresa.pk

    donde_trabaja = {
        m.empresa_id for m in membresias.empresas_de(norte.encargado.pk)
    }
    assert norte.empresa.pk in donde_trabaja

    with empresa(norte.empresa.pk):
        assert seguridad.permisos_de(norte.membresia.pk)


def test_hereda_el_nit_de_su_padre(farmacia_vida, datos_de_norte):
    """En Bolivia una sucursal comparte el NIT de su matriz, así que no se
    pide: se copia."""
    norte = alta_de_sucursal.dar_de_alta(datos_de_norte)

    assert norte.empresa.ident_tributaria == farmacia_vida.empresa.ident_tributaria


def test_no_se_pone_de_encargado_a_alguien_de_otro_cliente(
    farmacia_vida, datos_de_norte, crear_empresa
):
    ajena = Usuario.objects.create_user(
        username="ana.quispe",
        email="ana@olimpo.bo",
        password="Zq4tRn8Vd3",
        matriz=crear_empresa("Gimnasio Olimpo"),
    )
    datos = dataclasses.replace(datos_de_norte, encargado_username=ajena.username)

    with pytest.raises(ValidationError, match="no es una persona de ese cliente"):
        alta_de_sucursal.dar_de_alta(datos)


def test_un_rol_que_no_existe_en_la_matriz_corta(farmacia_vida, datos_de_norte):
    """Los roles se ven por ámbito: en una sucursal recién creada solo sirven
    los de la matriz. Asignar uno inexistente dejaría al encargado sin ver
    nada."""
    datos = dataclasses.replace(datos_de_norte, rol="Encargado de turno")

    with pytest.raises(ValidationError, match="No existe el rol"):
        alta_de_sucursal.dar_de_alta(datos)
