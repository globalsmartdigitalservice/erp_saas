"""Las consultas de roles, permisos, equipos y horarios."""

import datetime
from collections import defaultdict

import strawberry

from core.tenancy import empresa_actual
from dominios.seguridad import api as seguridad

from comun.catalogo_modulos import api as modulos
from comun.membresias import api as membresias
from comun.membresias.graphql.types import EmpresaDelUsuarioType
from comun.usuarios.graphql.types import UsuarioType

from dominios.seguridad.permisos import auto_permisos
from dominios.seguridad.permisos_graphql import (
    permisos_otorgables,
    requiere_autenticacion,
    requiere_permiso,
)

from .tipos_acceso import (
    DispositivoAutorizadoType,
    DispositivoType,
    ExcepcionHorarioType,
    HorarioAccesoType,
    VeredictoType,
)
from .types import (
    MiembroType,
    PermisoDeCatalogoType,
    PermisoDelRolType,
    RolAsignadoType,
    RolType,
)


def _funcionalidades_por_permiso() -> dict[int, modulos.Funcionalidad]:
    return {
        funcionalidad.auth_permission_id: funcionalidad
        for funcionalidad in modulos.listar_funcionalidades()
    }


@strawberry.type
class SeguridadQueries:
    @strawberry.field(
        description=(
            "Los roles que esta empresa puede usar: los suyos y los que "
            "hereda de su casa matriz. `esHeredado` dice cuáles no puede "
            "editar."
        )
    )
    @requiere_autenticacion
    def roles(
        self, info: strawberry.Info, estado_id: strawberry.ID | None = None
    ) -> list[RolType]:
        activa = empresa_actual()
        filas = seguridad.listar_roles_con_conteo(
            int(estado_id) if estado_id is not None else None
        )
        return [RolType.desde_modelo(r, activa) for r in filas]

    @strawberry.field(description="Un rol por su id.")
    @requiere_autenticacion
    def rol(self, info: strawberry.Info, id: strawberry.ID) -> RolType | None:
        fila = seguridad.obtener_rol(int(id))
        return RolType.desde_modelo(fila, empresa_actual()) if fila else None

    @strawberry.field(
        description="Qué puede hacer un rol. Funciona también con los heredados."
    )
    @requiere_autenticacion
    def permisos_del_rol(
        self, info: strawberry.Info, rol_id: strawberry.ID
    ) -> list[PermisoDelRolType]:
        return [
            PermisoDelRolType.desde_modelo(linea)
            for linea in seguridad.listar_permisos_del_rol(int(rol_id))
        ]

    @strawberry.field(
        description=(
            "Los permisos que usted puede ponerle a un rol: los suyos, porque "
            "nadie otorga lo que no tiene. `pantalla` y `modulo` llegan vacíos "
            "mientras el catálogo de módulos no tenga ese permiso."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_roles_agregar_permiso_al_rol")
    def catalogo_de_permisos(
        self, info: strawberry.Info
    ) -> list[PermisoDeCatalogoType]:
        otorgables = permisos_otorgables(info)
        funcionalidades = _funcionalidades_por_permiso()
        return [
            PermisoDeCatalogoType.desde_modelo(
                permiso, funcionalidades.get(permiso.pk)
            )
            for permiso in seguridad.listar_catalogo_de_permisos()
            if otorgables is None
            or f"{permiso.content_type.app_label}.{permiso.codename}" in otorgables
        ]

    @strawberry.field(
        description=(
            "Todos los roles que tuvo una persona en esta empresa, vigentes y "
            "terminados. Es el historial: quién le dio qué, cuándo y por qué."
        )
    )
    @requiere_autenticacion
    def roles_de(
        self, info: strawberry.Info, membresia_id: strawberry.ID
    ) -> list[RolAsignadoType]:
        activa = empresa_actual()
        return [
            RolAsignadoType.desde_modelo(
                a, RolType.desde_modelo(a.grupo_empresa, activa)
            )
            for a in seguridad.historial_de(int(membresia_id))
        ]

    @strawberry.field(
        description=(
            "Los códigos de permiso que OTRA persona tiene hoy en esta "
            "empresa, unidos de todos sus roles vigentes. Para los propios "
            "está `misPermisos`, que no pide nada."
        )
    )
    @requiere_autenticacion
    def permisos_de(
        self, info: strawberry.Info, membresia_id: strawberry.ID
    ) -> list[str]:
        return sorted(seguridad.permisos_de(int(membresia_id)))


@strawberry.type
class MiembroQueries:
    @strawberry.field(
        description=(
            "Quiénes trabajan en la empresa activa, cada uno con sus roles "
            "vigentes. NO devuelve gente de otros clientes."
        )
    )
    @requiere_autenticacion
    @requiere_permiso("segu_miembros_listar")
    @auto_permisos(recurso="SEGU_MIEMBROS", operacion="listar")
    def miembros(
        self, info: strawberry.Info, estado_id: strawberry.ID | None = None
    ) -> list[MiembroType]:
        filas = membresias.listar_membresias(
            int(estado_id) if estado_id is not None else None
        )
        activa = empresa_actual()
        roles = defaultdict(list)
        for asignacion in seguridad.roles_vigentes_de_varias_membresias(
            [fila.pk for fila in filas]
        ):
            roles[asignacion.usuario_empresa_id].append(
                RolType.desde_modelo(asignacion.grupo_empresa, activa)
            )
        return [MiembroType.desde_modelo(fila, roles[fila.pk]) for fila in filas]


@strawberry.type
class AccesoQueries:
    @strawberry.field(description="Los equipos registrados en esta empresa.")
    @requiere_autenticacion
    def dispositivos(
        self,
        info: strawberry.Info,
        estado_id: strawberry.ID | None = None,
    ) -> list[DispositivoType]:
        return [
            DispositivoType.desde_modelo(d)
            for d in seguridad.listar_dispositivos(
                int(estado_id) if estado_id is not None else None
            )
        ]

    @strawberry.field(
        description="Los equipos de una persona acá, autorizados y dados de baja."
    )
    @requiere_autenticacion
    def dispositivos_de(
        self,
        info: strawberry.Info,
        membresia_id: strawberry.ID,
    ) -> list[DispositivoAutorizadoType]:
        return [
            DispositivoAutorizadoType.desde_modelo(a)
            for a in seguridad.dispositivos_de(int(membresia_id))
        ]

    @strawberry.field(
        description=(
            "Los horarios de una persona. `cruzaMedianoche` viene calculado: "
            "el turno noche (22:00 a 06:00) es válido y no hay que rechazarlo "
            "en la pantalla."
        )
    )
    @requiere_autenticacion
    def horarios_de(
        self, info: strawberry.Info, membresia_id: strawberry.ID
    ) -> list[HorarioAccesoType]:
        return [
            HorarioAccesoType.desde_modelo(h)
            for h in seguridad.horarios_de(int(membresia_id))
        ]

    @strawberry.field(description="Los días sueltos: PERMISO o BLOQUEO.")
    @requiere_autenticacion
    def excepciones_de(
        self,
        info: strawberry.Info,
        membresia_id: strawberry.ID,
    ) -> list[ExcepcionHorarioType]:
        return [
            ExcepcionHorarioType.desde_modelo(e)
            for e in seguridad.excepciones_de(int(membresia_id))
        ]

    @strawberry.field(
        description=(
            "¿Esta persona puede entrar ahora, desde acá? Junta horario, "
            "excepciones y equipo autorizado. NO reemplaza a la contraseña ni "
            "decide permisos. `mac` la manda el cliente instalado en la PC; "
            "sin ella no se comprueba el equipo."
        )
    )
    @requiere_autenticacion
    def puede_entrar(
        self,
        info: strawberry.Info,
        membresia_id: strawberry.ID,
        momento: datetime.datetime | None = None,
        mac: str | None = None,
        ip_publica: str | None = None,
    ) -> VeredictoType:
        return VeredictoType.desde_modelo(
            seguridad.puede_entrar(
                membresia_id=int(membresia_id),
                momento=momento,
                mac=mac,
                ip_publica=ip_publica,
            )
        )


def _mi_membresia(info):
    """La membresía de quien llama, en la empresa donde está parado."""
    usuario = getattr(info.context.request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return None
    return membresias.membresia_de(usuario.pk)


@strawberry.type
class SesionQueries:
    @strawberry.field(
        description=(
            "Quién está conectado y en qué empresa, según el token de la "
            "cookie. `null` si no hay sesión. Es lo primero que pregunta el "
            "frontend al cargar, para saber si mostrar el login."
        )
    )
    def me(self, info: strawberry.Info) -> UsuarioType | None:
        usuario = getattr(info.context.request, "user", None)
        if usuario is None or not usuario.is_authenticated:
            return None
        return UsuarioType.desde_modelo(usuario)

    @strawberry.field(
        description=(
            "El id de la empresa en la que está parada la sesión. Sale del "
            "token, no de un parámetro: por eso cambiar de empresa exige "
            "entrar de nuevo."
        )
    )
    def empresa_actual(self) -> strawberry.ID | None:
        actual = empresa_actual()
        return strawberry.ID(str(actual)) if actual is not None else None

    @strawberry.field(
        description=(
            "La empresa de la sesión, con la razón social ya resuelta para "
            "el encabezado. `empresaActual` devuelve solo el id."
        )
    )
    def mi_empresa(self, info: strawberry.Info) -> EmpresaDelUsuarioType | None:
        membresia = _mi_membresia(info)
        return EmpresaDelUsuarioType.desde_modelo(membresia) if membresia else None

    @strawberry.field(
        description=(
            "Los códigos de permiso de quien está conectado, deducidos de la "
            "sesión. Sirve para esconder los botones que no va a poder usar; "
            "lo que de verdad protege son las guardas del backend."
        )
    )
    def mis_permisos(self, info: strawberry.Info) -> list[str]:
        membresia = _mi_membresia(info)
        return sorted(seguridad.permisos_de(membresia.pk)) if membresia else []


@strawberry.type
class SeguridadQuery(SeguridadQueries, AccesoQueries, SesionQueries):
    pass


@strawberry.type
class MiembroQuery(MiembroQueries):
    pass
