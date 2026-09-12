import datetime

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

from comun.membresias import api as membresias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_EXCEPCION_BLOQUEO,
    NOMBRE_EXCEPCION_PERMISO,
)
from core.tenancy import empresa
from dominios.seguridad import api as seguridad

pytestmark = pytest.mark.django_db

Usuario = get_user_model()

# Un lunes cualquiera, para que los cálculos de día no dependan de "hoy".
LUNES = datetime.date(2026, 9, 7)
MARTES = datetime.date(2026, 9, 8)


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def tipo_pc(catalogo):
    return catalogo["tipologia"](AGRUPADOR.TIPO_DISPOSITIVO, "PC de escritorio")


@pytest.fixture
def permiso_exc(catalogo):
    return catalogo["tipologia"](
        AGRUPADOR.TIPO_EXCEPCION_HORARIO, NOMBRE_EXCEPCION_PERMISO
    )


@pytest.fixture
def bloqueo_exc(catalogo):
    return catalogo["tipologia"](
        AGRUPADOR.TIPO_EXCEPCION_HORARIO, NOMBRE_EXCEPCION_BLOQUEO
    )


@pytest.fixture
def juan(empresa_a):
    return Usuario.objects.create_user(
        username="juan",
        email="juan@acme.com",
        password="Kx7pLm9Qw2",
        matriz=empresa_a,
    )


@pytest.fixture
def en_gimnasio(juan, empresa_a, activo):
    return membresias.afiliar(
        usuario_id=juan.id, empresa_id=empresa_a.id, estado_id=activo.id
    )


@pytest.fixture
def en_sucursal(juan, sucursal_a, activo):
    """La misma persona en OTRA empresa de su cliente.

    El caso real: trabaja de mañana en una sucursal y de tarde en la otra,
    con horarios y equipos distintos en cada una."""
    return membresias.afiliar(
        usuario_id=juan.id, empresa_id=sucursal_a.id, estado_id=activo.id
    )


def _a_las(fecha: datetime.date, hora: str) -> datetime.datetime:
    h, m = hora.split(":")
    return datetime.datetime.combine(fecha, datetime.time(int(h), int(m)))


def test_sin_horarios_cargados_se_puede_entrar_siempre(en_gimnasio, empresa_a):
    with empresa(empresa_a.id):
        assert seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "03:00")
        )


def test_dentro_del_horario_entra(en_gimnasio, empresa_a, activo):
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,  # lunes
            hora_inicio=datetime.time(8, 0),
            hora_fin=datetime.time(12, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )

        assert seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "09:30")
        )


def test_fuera_del_horario_no_entra_y_dice_por_que(en_gimnasio, empresa_a, activo):
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,
            hora_inicio=datetime.time(8, 0),
            hora_fin=datetime.time(12, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )

        veredicto = seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "15:00")
        )

    assert not veredicto
    assert "Fuera del horario" in veredicto.motivo


def test_otro_dia_de_la_semana_no_entra(en_gimnasio, empresa_a, activo):
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,  # solo lunes
            hora_inicio=datetime.time(8, 0),
            hora_fin=datetime.time(12, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )

        assert not seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(MARTES, "09:30")
        )


@pytest.fixture
def turno_noche(en_gimnasio, empresa_a, activo):
    """Lunes 22:00 → 06:00 del martes. La farmacia de guardia."""
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,  # lunes
            hora_inicio=datetime.time(22, 0),
            hora_fin=datetime.time(6, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )
    return en_gimnasio


def test_el_turno_noche_deja_entrar_antes_de_medianoche(
    turno_noche, empresa_a
):
    with empresa(empresa_a.id):
        assert seguridad.puede_entrar(
            membresia_id=turno_noche.id, momento=_a_las(LUNES, "23:30")
        )


def test_el_turno_noche_deja_entrar_DESPUES_de_medianoche(turno_noche, empresa_a):
    with empresa(empresa_a.id):
        assert seguridad.puede_entrar(
            membresia_id=turno_noche.id, momento=_a_las(MARTES, "01:00")
        )


def test_el_turno_noche_no_deja_entrar_a_media_tarde(turno_noche, empresa_a):
    with empresa(empresa_a.id):
        assert not seguridad.puede_entrar(
            membresia_id=turno_noche.id, momento=_a_las(LUNES, "15:00")
        )


def test_un_tramo_de_duracion_cero_se_rechaza(en_gimnasio, empresa_a, activo):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="duración cero"):
            seguridad.cargar_horario(
                membresia_id=en_gimnasio.id,
                dia_semana=0,
                hora_inicio=datetime.time(8, 0),
                hora_fin=datetime.time(8, 0),
                estado_id=activo.id,
            )


def test_un_permiso_deja_entrar_fuera_de_horario(
    en_gimnasio, empresa_a, activo, permiso_exc
):
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,
            hora_inicio=datetime.time(8, 0),
            hora_fin=datetime.time(12, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )
        seguridad.cargar_excepcion(
            membresia_id=en_gimnasio.id,
            fecha=LUNES,
            tipo_id=permiso_exc.id,
            estado_id=activo.id,
            motivo="inventario anual",
        )

        assert seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "22:00")
        )


def test_un_bloqueo_impide_entrar_aunque_este_en_horario(
    en_gimnasio, empresa_a, activo, bloqueo_exc
):
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,
            hora_inicio=datetime.time(8, 0),
            hora_fin=datetime.time(12, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )
        seguridad.cargar_excepcion(
            membresia_id=en_gimnasio.id,
            fecha=LUNES,
            tipo_id=bloqueo_exc.id,
            estado_id=activo.id,
            motivo="vacaciones",
        )

        veredicto = seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "09:00")
        )

    assert not veredicto
    assert "vacaciones" in veredicto.motivo


def test_si_hay_permiso_y_bloqueo_el_mismo_dia_gana_el_bloqueo(
    en_gimnasio, empresa_a, activo, permiso_exc, bloqueo_exc
):
    with empresa(empresa_a.id):
        for tipo in (permiso_exc, bloqueo_exc):
            seguridad.cargar_excepcion(
                membresia_id=en_gimnasio.id,
                fecha=LUNES,
                tipo_id=tipo.id,
                estado_id=activo.id,
            )

        assert not seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "09:00")
        )


def test_la_excepcion_con_horas_solo_vale_en_ese_tramo(
    en_gimnasio, empresa_a, activo, bloqueo_exc
):
    with empresa(empresa_a.id):
        seguridad.cargar_excepcion(
            membresia_id=en_gimnasio.id,
            fecha=LUNES,
            tipo_id=bloqueo_exc.id,
            estado_id=activo.id,
            hora_inicio=datetime.time(14, 0),
            hora_fin=datetime.time(16, 0),
        )

        assert not seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "15:00")
        )
        # Fuera del tramo bloqueado, y sin horarios: entra.
        assert seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "10:00")
        )


def test_una_excepcion_con_media_hora_se_rechaza(
    en_gimnasio, empresa_a, activo, bloqueo_exc
):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="las dos horas o ninguna"):
            seguridad.cargar_excepcion(
                membresia_id=en_gimnasio.id,
                fecha=LUNES,
                tipo_id=bloqueo_exc.id,
                estado_id=activo.id,
                hora_inicio=datetime.time(14, 0),
            )


def test_el_tipo_de_excepcion_tiene_que_ser_del_agrupador_correcto(
    en_gimnasio, empresa_a, activo, catalogo
):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="Se esperaba un tipo de excepción"):
            seguridad.cargar_excepcion(
                membresia_id=en_gimnasio.id,
                fecha=LUNES,
                tipo_id=catalogo["rubro"].id,
                estado_id=activo.id,
            )


def test_el_horario_de_una_sucursal_no_vale_en_la_otra(
    en_gimnasio, en_sucursal, empresa_a, sucursal_a, activo
):
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,
            hora_inicio=datetime.time(8, 0),
            hora_fin=datetime.time(12, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )
    with empresa(sucursal_a.id):
        seguridad.cargar_horario(
            membresia_id=en_sucursal.id,
            dia_semana=0,
            hora_inicio=datetime.time(14, 0),
            hora_fin=datetime.time(18, 0),
            estado_id=activo.id,
            vigencia_desde=LUNES,
        )

    a_las_tres = _a_las(LUNES, "15:00")

    with empresa(empresa_a.id):
        assert not seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=a_las_tres
        )
    with empresa(sucursal_a.id):
        assert seguridad.puede_entrar(
            membresia_id=en_sucursal.id, momento=a_las_tres
        )


def test_una_empresa_no_ve_los_horarios_de_la_otra(
    en_gimnasio, en_sucursal, empresa_a, sucursal_a, activo
):
    with empresa(empresa_a.id):
        seguridad.cargar_horario(
            membresia_id=en_gimnasio.id,
            dia_semana=0,
            hora_inicio=datetime.time(8, 0),
            hora_fin=datetime.time(12, 0),
            estado_id=activo.id,
        )

    with empresa(sucursal_a.id):
        assert seguridad.horarios_de(en_sucursal.id) == []


@pytest.fixture
def caja_2(empresa_a, activo, tipo_pc):
    with empresa(empresa_a.id):
        return seguridad.registrar_dispositivo(
            nombre="Caja 2",
            tipo_id=tipo_pc.id,
            estado_id=activo.id,
            mac="00-1b-44-11-3a-b7",
            ip="190.104.1.10",
        )


def test_la_mac_se_normaliza(caja_2):
    assert caja_2.mac == "00:1B:44:11:3A:B7"


def test_una_mac_con_forma_invalida_se_rechaza(empresa_a, activo, tipo_pc):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="forma de dirección MAC"):
            seguridad.registrar_dispositivo(
                nombre="Rara",
                tipo_id=tipo_pc.id,
                estado_id=activo.id,
                mac="no soy una mac",
            )


def test_el_equipo_autorizado_deja_entrar(en_gimnasio, empresa_a, activo, caja_2):
    with empresa(empresa_a.id):
        seguridad.autorizar_dispositivo(
            membresia_id=en_gimnasio.id,
            dispositivo_id=caja_2.id,
            estado_id=activo.id,
            fecha_inicio=LUNES,
        )

        assert seguridad.puede_entrar(
            membresia_id=en_gimnasio.id,
            momento=_a_las(LUNES, "09:00"),
            mac="00:1B:44:11:3A:B7",
            ip_publica="190.104.1.10",
        )


def test_un_equipo_no_autorizado_no_deja_entrar(en_gimnasio, empresa_a, caja_2):
    with empresa(empresa_a.id):
        veredicto = seguridad.puede_entrar(
            membresia_id=en_gimnasio.id,
            momento=_a_las(LUNES, "09:00"),
            mac="AA:BB:CC:DD:EE:FF",
        )

    assert not veredicto
    assert "no está autorizado" in veredicto.motivo


def test_la_mac_copiada_desde_otra_red_no_alcanza(
    en_gimnasio, empresa_a, activo, caja_2
):
    with empresa(empresa_a.id):
        seguridad.autorizar_dispositivo(
            membresia_id=en_gimnasio.id,
            dispositivo_id=caja_2.id,
            estado_id=activo.id,
            fecha_inicio=LUNES,
        )

        veredicto = seguridad.puede_entrar(
            membresia_id=en_gimnasio.id,
            momento=_a_las(LUNES, "09:00"),
            mac="00:1B:44:11:3A:B7",
            ip_publica="181.115.99.99",  # desde la casa
        )

    assert not veredicto
    assert "otra red" in veredicto.motivo


def test_sin_cliente_instalado_no_se_comprueba_el_equipo(
    en_gimnasio, empresa_a, caja_2
):
    with empresa(empresa_a.id):
        assert seguridad.puede_entrar(
            membresia_id=en_gimnasio.id, momento=_a_las(LUNES, "09:00")
        )


def test_no_se_puede_autorizar_el_equipo_de_otro_cliente(
    en_gimnasio, empresa_a, empresa_b, activo, tipo_pc
):
    with empresa(empresa_b.id):
        ajeno = seguridad.registrar_dispositivo(
            nombre="Caja de la farmacia",
            tipo_id=tipo_pc.id,
            estado_id=activo.id,
            mac="AA:BB:CC:DD:EE:FF",
        )

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError, match="no está disponible"):
            seguridad.autorizar_dispositivo(
                membresia_id=en_gimnasio.id,
                dispositivo_id=ajeno.id,
                estado_id=activo.id,
            )


def test_desautorizar_no_borra_la_fila(en_gimnasio, empresa_a, activo, caja_2, catalogo):
    from comun.tipologias.constantes import NOMBRE_ESTADO_BAJA

    catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)

    with empresa(empresa_a.id):
        autorizacion = seguridad.autorizar_dispositivo(
            membresia_id=en_gimnasio.id,
            dispositivo_id=caja_2.id,
            estado_id=activo.id,
        )
        quitada = seguridad.desautorizar_dispositivo(
            autorizacion_id=autorizacion.id
        )

        assert quitada.id == autorizacion.id
        assert quitada.fecha_fin == datetime.date.today()
        assert len(seguridad.dispositivos_de(en_gimnasio.id)) == 1


def test_sin_momento_la_hora_sale_de_TIME_ZONE_y_no_del_servidor(
    en_gimnasio, empresa_a, activo
):
    """El único test que NO pasa `momento`, y por eso el único que toca el
    reloj de verdad.

    El contenedor corre en UTC y la empresa en `America/La_Paz`: son cuatro
    horas. Con `datetime.now()` un turno de 08:00 a 17:00 dejaba entrar de
    04:00 a 13:00 y rechazaba el resto, sin excepción ni log — el veredicto
    salía mal y parecía bien.

    Se cargan los SIETE días para que el día no participe: lo único que puede
    hacer fallar esto es que la hora se lea en la zona equivocada."""
    with timezone.override("Pacific/Kiritimati"):
        alla = timezone.localtime()

        with empresa(empresa_a.id):
            for dia in range(7):
                seguridad.cargar_horario(
                    membresia_id=en_gimnasio.id,
                    dia_semana=dia,
                    hora_inicio=(alla - datetime.timedelta(minutes=5)).time(),
                    hora_fin=(alla + datetime.timedelta(minutes=5)).time(),
                    estado_id=activo.id,
                    vigencia_desde=datetime.date(2020, 1, 1),
                )

            assert seguridad.puede_entrar(membresia_id=en_gimnasio.id)
