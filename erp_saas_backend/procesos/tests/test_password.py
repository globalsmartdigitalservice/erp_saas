import pytest
from django.core.exceptions import ValidationError

from comun.empresas.services.empresa import NOMBRE_TIPO_SUCURSAL
from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from comun.usuarios import api as usuarios
from config.schema import schema
from core.tenancy import empresa, sin_filtro_de_empresa
from core.tests.afiliacion import afiliar_en
from core.tests.contexto_graphql import Contexto
from dominios.seguridad.models import SesionAcceso
from dominios.seguridad.services import login
from procesos import alta_de_sucursal, cambio_de_password, reseteo_de_password

pytestmark = pytest.mark.django_db

PASSWORD_NUEVA = "Kx7pLm9Qw2"
PASSWORD_DEL_CAJERO = "Zq4tRn8Vd3"

CAMBIAR = """
mutation ($datos: CambiarMiPasswordInput!) {
  cambiarMiPassword(datos: $datos)
}
"""


@pytest.fixture
def carla(farmacia_vida):
    """La administradora del cliente, con su contraseña temporal recién dada."""
    return farmacia_vida.administrador


@pytest.fixture
def cajero(farmacia_vida, catalogo_de_altas):
    """Alguien de la empresa SIN ningún rol, o sea sin ningún permiso."""
    with empresa(farmacia_vida.empresa.pk):
        persona = usuarios.crear_usuario(
            username="beto.quispe",
            email="beto@vida.bo",
            password=PASSWORD_DEL_CAJERO,
        )
    afiliar_en(
        farmacia_vida.empresa.pk,
        usuario_id=persona.pk,
        estado_id=catalogo_de_altas["estado_activo"].pk,
    )
    return persona


@pytest.fixture
def con_sucursal(farmacia_vida, catalogo_de_altas):
    """Carla trabajando también en Norte: el caso de la cuenta en dos empresas."""
    tipo = tipologias.obtener_del_sistema(
        AGRUPADOR.TIPO_EMPRESA, NOMBRE_TIPO_SUCURSAL
    )
    return alta_de_sucursal.dar_de_alta(
        alta_de_sucursal.DatosDeLaSucursal(
            padre_id=farmacia_vida.empresa.pk,
            razon_social="Farmacia Vida - Norte",
            tipo_empresa_id=tipo.pk,
            encargado_username=farmacia_vida.administrador.username,
        )
    )


def _sesiones_abiertas(usuario_id: int) -> set[int]:
    with sin_filtro_de_empresa():
        return set(
            SesionAcceso.objects.filter(
                usuario_empresa__usuario_id=usuario_id, fin__isnull=True
            ).values_list("pk", flat=True)
        )


def test_cambiar_la_propia_no_exige_ningun_permiso(farmacia_vida, cajero):
    """La guarda es `@requiere_autenticacion` y tiene que quedarse así.

    El cajero no tiene ningún rol, así que no tiene ningún permiso. Con
    `@requiere_permiso` esta llamada fallaría, y un rol armado sin marcar ese
    permiso dejaría a esa persona sin poder cambiar su contraseña NUNCA. Peor
    con D4, que va a exigírsela: el sistema le pediría algo que no lo deja
    hacer."""
    with empresa(farmacia_vida.empresa.pk):
        resultado = schema.execute_sync(
            CAMBIAR,
            variable_values={
                "datos": {
                    "passwordActual": PASSWORD_DEL_CAJERO,
                    "passwordNueva": PASSWORD_NUEVA,
                }
            },
            context_value=Contexto(cajero),
        )

    assert resultado.errors is None, resultado.errors
    cajero.refresh_from_db()
    assert cajero.check_password(PASSWORD_NUEVA)


def test_el_cambio_propio_deja_viva_mi_sesion_y_cierra_las_otras(
    farmacia_vida, carla, con_sucursal
):
    """Si la contraseña se filtró, cambiarla sin echar a quien la esté usando
    no sirve de nada. La propia se conserva para no obligar a entrar de nuevo
    justo después de hacer lo que el sistema pidió."""
    esta = login.ingresar(
        identificador=carla.username,
        password=farmacia_vida.password_temporal,
        empresa_id=farmacia_vida.empresa.pk,
    )
    login.ingresar(
        identificador=carla.username,
        password=farmacia_vida.password_temporal,
        empresa_id=con_sucursal.empresa.pk,
    )
    assert len(_sesiones_abiertas(carla.pk)) == 2

    cambio_de_password.cambiar(
        usuario_id=carla.pk,
        sesion_id=esta.sesion.pk,
        password_actual=farmacia_vida.password_temporal,
        password_nueva=PASSWORD_NUEVA,
    )

    assert _sesiones_abiertas(carla.pk) == {esta.sesion.pk}


def test_el_reseteo_la_saca_de_TODAS_sus_empresas(
    farmacia_vida, carla, con_sucursal
):
    """La contraseña es de la CUENTA, no de la membresía. Un reseteo pedido
    desde la matriz tiene que sacarla también de la sucursal: si no, sigue
    trabajando en Norte con una clave que ya no es suya."""
    for donde in (farmacia_vida.empresa.pk, con_sucursal.empresa.pk):
        login.ingresar(
            identificador=carla.username,
            password=farmacia_vida.password_temporal,
            empresa_id=donde,
        )
    assert len(_sesiones_abiertas(carla.pk)) == 2

    with empresa(farmacia_vida.empresa.pk):
        hecho = reseteo_de_password.resetear(membresia_id=farmacia_vida.membresia.pk)

    assert _sesiones_abiertas(carla.pk) == set()
    carla.refresh_from_db()
    assert carla.check_password(hecho.password)
    assert carla.debe_cambiar_password is True


def test_no_se_resetea_a_alguien_de_otra_empresa(farmacia_vida, con_sucursal):
    """Se llega a la persona por su MEMBRESÍA, y las membresías de otra
    empresa no existen para el manager de tenancy. El mensaje es el mismo que
    si el id no existiera: decir "esa es de otra sucursal" delata."""
    with empresa(con_sucursal.empresa.pk):
        assert membresias.obtener_membresia(con_sucursal.membresia.pk) is not None

        with pytest.raises(ValidationError, match="No existe la membresía"):
            reseteo_de_password.resetear(membresia_id=farmacia_vida.membresia.pk)
