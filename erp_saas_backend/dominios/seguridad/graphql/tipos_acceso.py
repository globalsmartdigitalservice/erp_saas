"""Los tipos de dispositivos, horarios y el veredicto de acceso."""

import datetime

import strawberry


@strawberry.type(name="Dispositivo")
class DispositivoType:
    """
    Un equipo de la empresa.

     `mac` e `ip` VIAJAN, y hay que tenerlo presente: son datos que
    identifican equipos de un cliente. El manager ya impide ver los de
    otro, pero cuando existan los permisos, esta pantalla debería pedir
    uno — no es información para cualquier empleado.
    """

    id: strawberry.ID
    nombre: str
    tipo_id: strawberry.ID
    mac: str
    ip: str | None
    identificador: str
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, dispositivo) -> "DispositivoType":
        return cls(
            id=strawberry.ID(str(dispositivo.pk)),
            nombre=dispositivo.nombre,
            tipo_id=strawberry.ID(str(dispositivo.tipo_id)),
            mac=dispositivo.mac,
            ip=str(dispositivo.ip) if dispositivo.ip else None,
            identificador=dispositivo.identificador,
            estado_id=strawberry.ID(str(dispositivo.estado_id)),
        )


@strawberry.type(name="DispositivoAutorizado")
class DispositivoAutorizadoType:
    id: strawberry.ID
    dispositivo: DispositivoType | None
    fecha_inicio: datetime.date
    fecha_fin: datetime.date | None
    ultimo_acceso: datetime.datetime | None
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, autorizacion) -> "DispositivoAutorizadoType":
        return cls(
            id=strawberry.ID(str(autorizacion.pk)),
            dispositivo=DispositivoType.desde_modelo(autorizacion.dispositivo),
            fecha_inicio=autorizacion.fecha_inicio,
            fecha_fin=autorizacion.fecha_fin,
            ultimo_acceso=autorizacion.ultimo_acceso,
            estado_id=strawberry.ID(str(autorizacion.estado_id)),
        )


@strawberry.type(name="HorarioAcceso")
class HorarioAccesoType:
    """
     `cruza_medianoche` viaja calculado y no se deja al frontend: si la
    pantalla comparara las horas por su cuenta, mostraría el turno noche
    como un tramo vacío. Es una regla del dominio, no de la pantalla.
    """

    id: strawberry.ID
    dia_semana: int
    hora_inicio: datetime.time
    hora_fin: datetime.time
    cruza_medianoche: bool
    vigencia_desde: datetime.date
    vigencia_hasta: datetime.date | None
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, horario) -> "HorarioAccesoType":
        return cls(
            id=strawberry.ID(str(horario.pk)),
            dia_semana=horario.dia_semana,
            hora_inicio=horario.hora_inicio,
            hora_fin=horario.hora_fin,
            cruza_medianoche=horario.cruza_medianoche,
            vigencia_desde=horario.vigencia_desde,
            vigencia_hasta=horario.vigencia_hasta,
            estado_id=strawberry.ID(str(horario.estado_id)),
        )


@strawberry.type(name="ExcepcionHorario")
class ExcepcionHorarioType:
    id: strawberry.ID
    fecha: datetime.date
    tipo: str
    hora_inicio: datetime.time | None
    hora_fin: datetime.time | None
    es_dia_completo: bool
    motivo: str
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, excepcion) -> "ExcepcionHorarioType":
        return cls(
            id=strawberry.ID(str(excepcion.pk)),
            fecha=excepcion.fecha,
            # El NOMBRE y no el id: de esto depende que la excepción deje
            # entrar o lo impida, y la pantalla tiene que poder mostrarlo
            # sin resolver otra consulta.
            tipo=excepcion.tipo.nombre,
            hora_inicio=excepcion.hora_inicio,
            hora_fin=excepcion.hora_fin,
            es_dia_completo=excepcion.es_dia_completo,
            motivo=excepcion.motivo,
            estado_id=strawberry.ID(str(excepcion.estado_id)),
        )


@strawberry.type(name="Veredicto")
class VeredictoType:
    """
    El resultado de `puedeEntrar`.

     `motivo` es para quien ADMINISTRA, no necesariamente para la
    pantalla de login: decirle a un desconocido "estás fuera de horario"
    le confirma que ese usuario existe y le dibuja el sistema. Qué se
    muestra lo decide la pantalla.
    """

    permitido: bool
    motivo: str

    @classmethod
    def desde_modelo(cls, veredicto) -> "VeredictoType":
        return cls(permitido=veredicto.permitido, motivo=veredicto.motivo)
