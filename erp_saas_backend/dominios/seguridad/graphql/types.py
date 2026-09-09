"""Los tipos de roles y permisos que ve el frontend."""

import datetime

import strawberry


@strawberry.type(name="PermisoDelRol")
class PermisoDelRolType:
    """
    Una línea de "este rol puede hacer esto".

    `codigo` es lo que entiende `has_perm()` ("ventas.anular_factura") y
    `etiqueta` es lo que se muestra. Los dos viajan porque el frontend
    necesita el primero para comparar y el segundo para mostrar.
    """

    auth_permission_id: strawberry.ID
    codigo: str
    etiqueta: str

    @classmethod
    def desde_modelo(cls, linea) -> "PermisoDelRolType":
        permiso = linea.auth_permission
        return cls(
            auth_permission_id=strawberry.ID(str(permiso.pk)),
            codigo=f"{permiso.content_type.app_label}.{permiso.codename}",
            etiqueta=permiso.name,
        )


@strawberry.type(name="Rol")
class RolType:
    """
    Un rol de empresa.

     `es_heredado` es el campo que hace usable la pantalla: dice si el
    rol viene de la casa matriz. Sin él, el usuario vería un botón de
    editar que siempre falla — la sucursal ve el rol de su matriz pero no
    lo puede tocar.
    """

    id: strawberry.ID
    nombre: str
    estado_id: strawberry.ID
    es_heredado: bool
    cantidad_permisos: int | None

    @classmethod
    def desde_modelo(cls, rol, empresa_activa_id: int | None) -> "RolType":
        return cls(
            id=strawberry.ID(str(rol.pk)),
            nombre=rol.nombre,
            estado_id=strawberry.ID(str(rol.estado_id)),
            es_heredado=rol.empresa_id != empresa_activa_id,
            # Lo pone `listar_roles_con_conteo` con un annotate; en las
            # otras consultas no está y viaja como null en vez de
            # dispararse una consulta por rol.
            cantidad_permisos=getattr(rol, "cantidad_permisos", None),
        )


@strawberry.type(name="RolAsignado")
class RolAsignadoType:
    """
    Quién tiene qué rol, desde cuándo y por qué.

    El `motivo` y las fechas viajan porque son lo que hace legible el
    historial seis meses después: "¿quién le dio permiso de anular a
    Juan?" se contesta con esto.
    """

    id: strawberry.ID
    membresia_id: strawberry.ID
    rol: RolType | None
    fecha_inicio: datetime.date
    fecha_fin: datetime.date | None
    motivo: str
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, asignacion, rol: RolType | None) -> "RolAsignadoType":
        return cls(
            id=strawberry.ID(str(asignacion.pk)),
            membresia_id=strawberry.ID(str(asignacion.usuario_empresa_id)),
            rol=rol,
            fecha_inicio=asignacion.fecha_inicio,
            fecha_fin=asignacion.fecha_fin,
            motivo=asignacion.motivo,
            estado_id=strawberry.ID(str(asignacion.estado_id)),
        )
