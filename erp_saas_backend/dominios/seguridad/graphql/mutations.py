

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import (
    permisos_otorgables,
    requiere_autenticacion,
    requiere_permiso,
    usuario_de_la_sesion,
)

from core.tenancy import empresa_actual
from dominios.seguridad import api as seguridad

from .inputs import (
    ActualizarAsignacionInput,
    ActualizarRolInput,
    AsignarRolInput,
    CrearRolInput,
)
from .inputs_acceso import (
    AutorizarDispositivoInput,
    CargarExcepcionInput,
    CargarHorarioInput,
    RegistrarDispositivoInput,
)
from .tipos_acceso import (
    DispositivoAutorizadoType,
    DispositivoType,
    ExcepcionHorarioType,
    HorarioAccesoType,
)
from .types import PermisoDelRolType, RolAsignadoType, RolType


def _traducir(error: ValidationError) -> GraphQLError:
    return GraphQLError("; ".join(error.messages))


def _a_rol(fila) -> RolType:
    return RolType.desde_modelo(fila, empresa_actual())


def _autor(info) -> int:
    """Quién firma la fila. Sale de la sesión, nunca del input: si llegara
    de afuera, cualquiera le atribuiría el registro a otro."""
    return usuario_de_la_sesion(info).pk


@auto_permisos(recurso="SEGU_ROLES")
@strawberry.type
class SeguridadMutations:
    @strawberry.mutation(
        description="Crea un rol EN LA EMPRESA ACTIVA. La empresa no se manda."
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_crear_rol")
    def crear_rol(self, info: strawberry.Info, datos: CrearRolInput) -> RolType:
        try:
            fila = seguridad.crear_rol(
                nombre=datos.nombre, estado_id=int(datos.estado_id)
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_rol(fila)

    @strawberry.mutation(
        description=(
            "Edita un rol propio. Falla si es de la casa matriz: solo ella "
            "puede cambiarlo, porque el cambio les llega a todas sus "
            "sucursales."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_actualizar_rol")
    def actualizar_rol(
        self,
        info: strawberry.Info, id: strawberry.ID, datos: ActualizarRolInput
    ) -> RolType:
        try:
            fila = seguridad.actualizar_rol(int(id), nombre=datos.nombre)
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_rol(fila)

    @strawberry.mutation(
        description="Da de baja un rol. Falla si alguien todavía lo tiene."
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_desactivar_rol")
    def desactivar_rol(self, info: strawberry.Info, id: strawberry.ID) -> RolType:
        try:
            fila = seguridad.desactivar_rol(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_rol(fila)

    @strawberry.mutation(
        description="Vuelve a poner en servicio un rol dado de baja."
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_reactivar_rol")
    def reactivar_rol(self, info: strawberry.Info, id: strawberry.ID) -> RolType:
        try:
            fila = seguridad.reactivar_rol(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_rol(fila)

    @strawberry.mutation(
        description=(
            "Le agrega un permiso al rol y devuelve TODOS sus permisos. "
            "Marcarlo dos veces no falla ni duplica."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_agregar_permiso_al_rol")
    def agregar_permiso_al_rol(
        self,
        info: strawberry.Info, rol_id: strawberry.ID, auth_permission_id: strawberry.ID
    ) -> list[PermisoDelRolType]:
        try:
            lineas = seguridad.agregar_permiso(
                grupo_id=int(rol_id),
                auth_permission_id=int(auth_permission_id),
                otorgables=permisos_otorgables(info),
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return [PermisoDelRolType.desde_modelo(linea) for linea in lineas]

    @strawberry.mutation(
        description="Le quita un permiso al rol. Quitar lo que no estaba no falla."
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_quitar_permiso_del_rol")
    def quitar_permiso_del_rol(
        self,
        info: strawberry.Info, rol_id: strawberry.ID, auth_permission_id: strawberry.ID
    ) -> list[PermisoDelRolType]:
        try:
            lineas = seguridad.quitar_permiso(
                grupo_id=int(rol_id), auth_permission_id=int(auth_permission_id)
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return [PermisoDelRolType.desde_modelo(linea) for linea in lineas]

    @strawberry.mutation(
        description=(
            "Le da un rol a una persona. El rol puede ser de la casa matriz: "
            "es lo que permite definirlo una sola vez arriba y usarlo en "
            "todas las sucursales."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_asignar_rol")
    def asignar_rol(self, info: strawberry.Info, datos: AsignarRolInput) -> RolAsignadoType:
        try:
            fila = seguridad.asignar_rol(
                membresia_id=int(datos.membresia_id),
                grupo_id=int(datos.rol_id),
                estado_id=int(datos.estado_id),
                fecha_inicio=datos.fecha_inicio,
                fecha_fin=datos.fecha_fin,
                motivo=datos.motivo,
                asignado_por_id=_autor(info),
                otorgables=permisos_otorgables(info),
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return RolAsignadoType.desde_modelo(fila, _a_rol(fila.grupo_empresa))

    @strawberry.mutation(
        description=(
            "Cambia las fechas, el motivo o el estado de una asignación. Ni "
            "la persona ni el rol se cambian: eso ya es otra asignación."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_actualizar_asignacion")
    def actualizar_asignacion(
        self,
        info: strawberry.Info,
        asignacion_id: strawberry.ID,
        datos: ActualizarAsignacionInput,
    ) -> RolAsignadoType:
        campos = {}
        if datos.fecha_fin is not strawberry.UNSET:
            campos["fecha_fin"] = datos.fecha_fin
        if datos.motivo is not None:
            campos["motivo"] = datos.motivo
        if datos.estado_id is not None:
            campos["estado_id"] = int(datos.estado_id)

        try:
            fila = seguridad.actualizar_asignacion(int(asignacion_id), **campos)
        except ValidationError as error:
            raise _traducir(error) from error
        return RolAsignadoType.desde_modelo(fila, _a_rol(fila.grupo_empresa))

    @strawberry.mutation(
        description=(
            "Le saca el rol a una persona: le pone fecha de fin. NO borra la "
            "fila, porque es el historial de quién pudo qué."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_quitar_rol")
    def quitar_rol(self, info: strawberry.Info, asignacion_id: strawberry.ID) -> RolAsignadoType:
        try:
            fila = seguridad.quitar_rol(asignacion_id=int(asignacion_id))
        except ValidationError as error:
            raise _traducir(error) from error
        return RolAsignadoType.desde_modelo(fila, _a_rol(fila.grupo_empresa))


@auto_permisos(recurso="SEGU_EQUIPOS")
@strawberry.type
class AccesoMutations:
    """
    Equipos, horarios y excepciones.

    Va en su propia clase y con su propio `recurso` porque es OTRA
    pantalla: "quién puede hacer qué" y "desde dónde y cuándo puede
    entrar" se administran por separado, y los permisos para tocarlas
    tienen que poder darse por separado.
    """

    @strawberry.mutation(description="Da de alta un equipo en la empresa activa.")
    @requiere_autenticacion
    @requiere_permiso("segu_equipos_registrar_dispositivo")
    def registrar_dispositivo(
        self,
        info: strawberry.Info, datos: RegistrarDispositivoInput
    ) -> DispositivoType:
        try:
            fila = seguridad.registrar_dispositivo(
                nombre=datos.nombre,
                tipo_id=int(datos.tipo_id),
                estado_id=int(datos.estado_id),
                mac=datos.mac,
                ip=datos.ip,
                identificador=datos.identificador,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return DispositivoType.desde_modelo(fila)

    @strawberry.mutation(
        description=(
            "Le autoriza un equipo a una persona DE ESTA EMPRESA. El equipo "
            "también tiene que ser de esta empresa."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_equipos_autorizar_dispositivo")
    def autorizar_dispositivo(
        self,
        info: strawberry.Info, datos: AutorizarDispositivoInput
    ) -> DispositivoAutorizadoType:
        try:
            fila = seguridad.autorizar_dispositivo(
                membresia_id=int(datos.membresia_id),
                dispositivo_id=int(datos.dispositivo_id),
                estado_id=int(datos.estado_id),
                fecha_inicio=datos.fecha_inicio,
                fecha_fin=datos.fecha_fin,
                autorizado_por_id=_autor(info),
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return DispositivoAutorizadoType.desde_modelo(fila)

    @strawberry.mutation(
        description="Le quita el equipo. NO borra la fila: es historial."
    )
    @requiere_autenticacion
    @requiere_permiso("segu_equipos_desautorizar_dispositivo")
    def desautorizar_dispositivo(
        self,
        info: strawberry.Info, autorizacion_id: strawberry.ID
    ) -> DispositivoAutorizadoType:
        try:
            fila = seguridad.desautorizar_dispositivo(
                autorizacion_id=int(autorizacion_id)
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return DispositivoAutorizadoType.desde_modelo(fila)

    @strawberry.mutation(
        description=(
            "Carga un tramo horario. `horaFin` menor que `horaInicio` es "
            "VÁLIDO: es el turno que cruza la medianoche."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_equipos_cargar_horario")
    def cargar_horario(self, info: strawberry.Info, datos: CargarHorarioInput) -> HorarioAccesoType:
        try:
            fila = seguridad.cargar_horario(
                membresia_id=int(datos.membresia_id),
                dia_semana=datos.dia_semana,
                hora_inicio=datos.hora_inicio,
                hora_fin=datos.hora_fin,
                estado_id=int(datos.estado_id),
                vigencia_desde=datos.vigencia_desde,
                vigencia_hasta=datos.vigencia_hasta,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return HorarioAccesoType.desde_modelo(fila)

    @strawberry.mutation(description="Da de baja un tramo horario.")
    @requiere_autenticacion
    @requiere_permiso("segu_equipos_quitar_horario")
    def quitar_horario(self, info: strawberry.Info, horario_id: strawberry.ID) -> HorarioAccesoType:
        try:
            fila = seguridad.quitar_horario(horario_id=int(horario_id))
        except ValidationError as error:
            raise _traducir(error) from error
        return HorarioAccesoType.desde_modelo(fila)

    @strawberry.mutation(
        description="Un día suelto: PERMISO deja entrar, BLOQUEO lo impide."
    )
    @requiere_autenticacion
    @requiere_permiso("segu_equipos_cargar_excepcion")
    def cargar_excepcion(self, info: strawberry.Info, datos: CargarExcepcionInput) -> ExcepcionHorarioType:
        try:
            fila = seguridad.cargar_excepcion(
                membresia_id=int(datos.membresia_id),
                fecha=datos.fecha,
                tipo_id=int(datos.tipo_id),
                estado_id=int(datos.estado_id),
                hora_inicio=datos.hora_inicio,
                hora_fin=datos.hora_fin,
                motivo=datos.motivo,
                creado_por_id=_autor(info),
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return ExcepcionHorarioType.desde_modelo(fila)

    @strawberry.mutation(description="Da de baja una excepción.")
    @requiere_autenticacion
    @requiere_permiso("segu_equipos_quitar_excepcion")
    def quitar_excepcion(self, info: strawberry.Info, excepcion_id: strawberry.ID) -> ExcepcionHorarioType:
        try:
            fila = seguridad.quitar_excepcion(excepcion_id=int(excepcion_id))
        except ValidationError as error:
            raise _traducir(error) from error
        return ExcepcionHorarioType.desde_modelo(fila)


@strawberry.type
class SeguridadMutation(SeguridadMutations, AccesoMutations):
    pass
