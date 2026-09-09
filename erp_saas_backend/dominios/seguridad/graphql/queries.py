"""Las consultas de roles, permisos, equipos y horarios."""

import datetime

import strawberry

from core.tenancy import empresa_actual
from dominios.seguridad import api as seguridad

from comun.usuarios.graphql.types import UsuarioType

from .tipos_acceso import (
    DispositivoAutorizadoType,
    DispositivoType,
    ExcepcionHorarioType,
    HorarioAccesoType,
    VeredictoType,
)
from .types import PermisoDelRolType, RolAsignadoType, RolType


@strawberry.type
class SeguridadQueries:
    @strawberry.field(
        description=(
            "Los roles que esta empresa puede usar: los suyos y los que "
            "hereda de su casa matriz. `esHeredado` dice cuáles no puede "
            "editar."
        )
    )
    def roles(self, estado_id: strawberry.ID | None = None) -> list[RolType]:
        activa = empresa_actual()
        filas = seguridad.listar_roles_con_conteo(
            int(estado_id) if estado_id is not None else None
        )
        return [RolType.desde_modelo(r, activa) for r in filas]

    @strawberry.field(description="Un rol por su id.")
    def rol(self, id: strawberry.ID) -> RolType | None:
        fila = seguridad.obtener_rol(int(id))
        return RolType.desde_modelo(fila, empresa_actual()) if fila else None

    @strawberry.field(
        description="Qué puede hacer un rol. Funciona también con los heredados."
    )
    def permisos_del_rol(self, rol_id: strawberry.ID) -> list[PermisoDelRolType]:
        return [
            PermisoDelRolType.desde_modelo(linea)
            for linea in seguridad.listar_permisos_del_rol(int(rol_id))
        ]

    @strawberry.field(
        description=(
            "Todos los roles que tuvo una persona en esta empresa, vigentes y "
            "terminados. Es el historial: quién le dio qué, cuándo y por qué."
        )
    )
    def roles_de(self, membresia_id: strawberry.ID) -> list[RolAsignadoType]:
        activa = empresa_actual()
        return [
            RolAsignadoType.desde_modelo(
                a, RolType.desde_modelo(a.grupo_empresa, activa)
            )
            for a in seguridad.historial_de(int(membresia_id))
        ]

    @strawberry.field(
        description=(
            "Los códigos de permiso que una persona tiene HOY en esta "
            "empresa, ya unidos de todos sus roles vigentes. Es lo mismo que "
            "contesta `has_perm()`, y sirve para que el frontend esconda los "
            "botones que no va a poder usar."
        )
    )
    def mis_permisos(self, membresia_id: strawberry.ID) -> list[str]:
        return sorted(seguridad.permisos_de(int(membresia_id)))


@strawberry.type
class AccesoQueries:
    @strawberry.field(description="Los equipos registrados en esta empresa.")
    def dispositivos(
        self, estado_id: strawberry.ID | None = None
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
    def dispositivos_de(
        self, membresia_id: strawberry.ID
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
    def horarios_de(self, membresia_id: strawberry.ID) -> list[HorarioAccesoType]:
        return [
            HorarioAccesoType.desde_modelo(h)
            for h in seguridad.horarios_de(int(membresia_id))
        ]

    @strawberry.field(description="Los días sueltos: PERMISO o BLOQUEO.")
    def excepciones_de(
        self, membresia_id: strawberry.ID
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
    def puede_entrar(
        self,
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


@strawberry.type
class SesionQueries:
    @strawberry.field(
        description=(
            "Quién está conectado y en qué empresa, según el token de la "
            "cookie. `null` si no hay sesión. Es lo primero que pregunta el "
            "frontend al cargar, para saber si mostrar el login."
        )
    )
    def yo(self, info: strawberry.Info) -> UsuarioType | None:
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


@strawberry.type
class SeguridadQuery(SeguridadQueries, AccesoQueries, SesionQueries):
    pass
