"""
Acceso a datos de dispositivos y horarios.

Las cuatro tablas son `ModeloTenantDerivado` o `ModeloTenant`, así que el
filtro por empresa ya viene puesto: acá no se escribe ninguna condición
de empresa.

SOBRE EL N+1 — ESTAS CONSULTAS CORREN EN CADA INGRESO

`puede_entrar()` se llama una vez por login. No es el camino más caliente
del sistema, pero sí el más visible: si tarda, la gente lo nota al
entrar. Por eso cada función trae de una sola consulta todo lo que el
evaluador necesita, y las relaciones que va a leer vienen resueltas.
"""

import datetime

from django.db.models import Q

from dominios.seguridad.models import (
    Dispositivo,
    DispositivoUsuario,
    HorarioAcceso,
    HorarioExcepcion,
)


def horarios_vigentes(
    membresia_id: int, fecha: datetime.date, estado_id: int
) -> list[HorarioAcceso]:
    """
    Los horarios que rigen ESE día, de los SIETE días.

    Se traen todos y no solo los del día que se consulta, a propósito: el
    evaluador necesita también los del día ANTERIOR que cruzan la
    medianoche —a la 1 AM del martes manda el turno del lunes 22:00–06:00—
    y pedirlos aparte sería una segunda consulta.
    """
    return list(
        HorarioAcceso.objects.filter(
            usuario_empresa_id=membresia_id, estado_id=estado_id
        )
        .filter(vigencia_desde__lte=fecha)
        .filter(Q(vigencia_hasta__isnull=True) | Q(vigencia_hasta__gte=fecha))
    )


def listar_horarios(membresia_id: int) -> list[HorarioAcceso]:
    """Todos, vigentes o no. Es la pantalla de horarios de una persona."""
    return list(HorarioAcceso.objects.filter(usuario_empresa_id=membresia_id))


def hay_horario_igual(
    membresia_id: int,
    dia_semana: int,
    hora_inicio,
    hora_fin,
    excluir_id: int | None = None,
) -> bool:
    """Para no cargar dos veces exactamente el mismo tramo."""
    qs = HorarioAcceso.objects.filter(
        usuario_empresa_id=membresia_id,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
    )
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear_horario(**campos) -> HorarioAcceso:
    return HorarioAcceso.objects.create(**campos)


def actualizar_horario(horario: HorarioAcceso, **campos) -> HorarioAcceso:
    for campo, valor in campos.items():
        setattr(horario, campo, valor)
    horario.save(update_fields=list(campos))
    return horario


def obtener_horario(horario_id: int) -> HorarioAcceso | None:
    return HorarioAcceso.objects.filter(pk=horario_id).first()


def excepciones_del_dia(
    membresia_id: int, fecha: datetime.date, estado_id: int
) -> list[HorarioExcepcion]:
    """
    `tipo` viene RESUELTO: el evaluador lo compara por nombre para saber
    si la excepción deja entrar o lo impide, y sin `select_related` esa
    comparación dispara una consulta por excepción.
    """
    return list(
        HorarioExcepcion.objects.select_related("tipo").filter(
            usuario_empresa_id=membresia_id, fecha=fecha, estado_id=estado_id
        )
    )


def listar_excepciones(membresia_id: int) -> list[HorarioExcepcion]:
    return list(
        HorarioExcepcion.objects.select_related("tipo").filter(
            usuario_empresa_id=membresia_id
        )
    )


def obtener_excepcion(excepcion_id: int) -> HorarioExcepcion | None:
    return (
        HorarioExcepcion.objects.select_related("tipo")
        .filter(pk=excepcion_id)
        .first()
    )


def crear_excepcion(**campos) -> HorarioExcepcion:
    return HorarioExcepcion.objects.create(**campos)


def actualizar_excepcion(excepcion: HorarioExcepcion, **campos) -> HorarioExcepcion:
    for campo, valor in campos.items():
        setattr(excepcion, campo, valor)
    excepcion.save(update_fields=list(campos))
    return excepcion


def obtener_dispositivo(dispositivo_id: int) -> Dispositivo | None:
    return Dispositivo.objects.filter(pk=dispositivo_id).first()


def obtener_dispositivos(dispositivo_ids) -> dict[int, Dispositivo]:
    return {
        d.pk: d for d in Dispositivo.objects.filter(pk__in=list(dispositivo_ids))
    }


def listar_dispositivos(estado_id: int | None = None) -> list[Dispositivo]:
    qs = Dispositivo.objects.select_related("tipo")
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def existe_mac(mac: str, excluir_id: int | None = None) -> bool:
    qs = Dispositivo.objects.filter(mac=mac)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear_dispositivo(**campos) -> Dispositivo:
    return Dispositivo.objects.create(**campos)


def actualizar_dispositivo(dispositivo: Dispositivo, **campos) -> Dispositivo:
    for campo, valor in campos.items():
        setattr(dispositivo, campo, valor)
    dispositivo.save(update_fields=list(campos))
    return dispositivo


def autorizacion_vigente_por_mac(
    membresia_id: int, mac: str, fecha: datetime.date, estado_id: int
) -> DispositivoUsuario | None:
    """
    LA CONSULTA DEL INGRESO: ¿esta persona tiene autorizado el equipo
   con esta MAC, hoy?

   `dispositivo` viene resuelto porque justo después se compara su `ip`
   registrada: sin esto son dos consultas en el camino del login.
   """
    return (
        DispositivoUsuario.objects.select_related("dispositivo")
        .filter(
            usuario_empresa_id=membresia_id,
            dispositivo__mac=mac,
            estado_id=estado_id,
        )
        .filter(fecha_inicio__lte=fecha)
        .filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha))
        .first()
    )


def listar_autorizaciones(membresia_id: int) -> list[DispositivoUsuario]:
    """El historial completo de equipos de una persona en esta empresa."""
    return list(
        DispositivoUsuario.objects.select_related(
            "dispositivo", "dispositivo__tipo"
        ).filter(usuario_empresa_id=membresia_id)
    )


def hay_autorizacion_vigente(
    membresia_id: int, dispositivo_id: int, excluir_id: int | None = None
) -> bool:
    qs = DispositivoUsuario.objects.filter(
        usuario_empresa_id=membresia_id,
        dispositivo_id=dispositivo_id,
        fecha_fin__isnull=True,
    )
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def obtener_autorizacion(autorizacion_id: int) -> DispositivoUsuario | None:
    return (
        DispositivoUsuario.objects.select_related("dispositivo")
        .filter(pk=autorizacion_id)
        .first()
    )


def crear_autorizacion(**campos) -> DispositivoUsuario:
    return DispositivoUsuario.objects.create(**campos)


def actualizar_autorizacion(
    autorizacion: DispositivoUsuario, **campos
) -> DispositivoUsuario:
    for campo, valor in campos.items():
        setattr(autorizacion, campo, valor)
    autorizacion.save(update_fields=list(campos))
    return autorizacion
