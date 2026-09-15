import pytest
from django.core.exceptions import ValidationError

from comun.membresias import api as membresias
from core.tenancy import empresa
from dominios.seguridad import api as seguridad
from dominios.seguridad.services import login
from procesos import alta_de_cliente

pytestmark = pytest.mark.django_db


def test_el_cliente_nace_con_alguien_que_puede_entrar(farmacia_vida):
    """El invariante que sostiene todo el proceso, y la razón de que sea una
    sola transacción: una empresa sin nadie adentro es imposible de poblar
    después, porque para dar de alta a alguien hay que estar parado ahí.

    La falla sería SILENCIOSA: el comando imprimiría "cliente creado" en verde
    y nadie se entera hasta que el cliente llama diciendo que no puede entrar."""
    assert farmacia_vida.administrador.matriz_id == farmacia_vida.empresa.pk

    donde_trabaja = membresias.empresas_de(farmacia_vida.administrador.pk)
    assert [m.empresa_id for m in donde_trabaja] == [farmacia_vida.empresa.pk]

    with empresa(farmacia_vida.empresa.pk):
        assert seguridad.permisos_de(farmacia_vida.membresia.pk)


def test_la_contrasena_temporal_sirve_para_entrar(farmacia_vida):
    """De punta a punta: lo que imprime el comando abre una sesión de verdad."""
    resultado = login.login(
        identificador=farmacia_vida.administrador.username,
        password=farmacia_vida.password_temporal,
    )

    assert resultado.necesita_elegir_empresa is False
    assert resultado.sesion.usuario_empresa_id == farmacia_vida.membresia.pk


def test_entra_obligado_a_cambiar_la_contrasena(farmacia_vida):
    assert farmacia_vida.administrador.debe_cambiar_password is True


def test_sin_permisos_en_el_catalogo_no_se_crea_el_cliente(
    datos_del_cliente, datos_de_carla
):
    """Un rol sin permisos deja al administrador entrando a un sistema donde no
    ve nada, y eso se descubre tarde y del lado del cliente. Vale más cortar."""
    from django.contrib.auth.models import Permission

    from comun.empresas import api as empresas
    from dominios.seguridad.permisos import content_type_del_ancla

    Permission.objects.filter(content_type=content_type_del_ancla()).delete()

    with pytest.raises(ValidationError, match="generar_permisos"):
        alta_de_cliente.dar_de_alta(
            cliente=datos_del_cliente, administrador=datos_de_carla
        )

    assert empresas.listar_empresas() == []
