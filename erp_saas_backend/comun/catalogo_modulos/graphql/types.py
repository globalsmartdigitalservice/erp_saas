"""El árbol de módulos, pantallas y acciones que ve el frontend."""

import strawberry


@strawberry.type(name="Funcionalidad")
class FuncionalidadType:
    """Una ACCIÓN: lo que se puede hacer dentro de una pantalla."""

    id: strawberry.ID
    nombre: str
    descripcion: str
    auth_permission_id: strawberry.ID
    codigo_permiso: str
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, funcionalidad) -> "FuncionalidadType":
        permiso = funcionalidad.auth_permission
        return cls(
            id=strawberry.ID(str(funcionalidad.pk)),
            nombre=funcionalidad.nombre,
            descripcion=funcionalidad.descripcion,
            auth_permission_id=strawberry.ID(str(permiso.pk)),
            # El mismo formato que devuelve `misPermisos`, para que el
            # frontend pueda comparar sin traducir nada.
            codigo_permiso=f"{permiso.content_type.app_label}.{permiso.codename}",
            estado_id=strawberry.ID(str(funcionalidad.estado_id)),
        )


@strawberry.type(name="SubModulo")
class SubModuloType:
    """Una PANTALLA. Las `funcionalidades` viajan RESUELTAS y no como ids:
    pedirlas de a una sería una consulta por pantalla."""

    id: strawberry.ID
    codigo: str
    nombre: str
    ruta: str
    modulo_id: strawberry.ID
    estado_id: strawberry.ID
    funcionalidades: list[FuncionalidadType]

    @classmethod
    def desde_modelo(cls, sub_modulo, funcionalidades) -> "SubModuloType":
        return cls(
            id=strawberry.ID(str(sub_modulo.pk)),
            codigo=sub_modulo.codigo,
            nombre=sub_modulo.nombre,
            ruta=sub_modulo.ruta,
            modulo_id=strawberry.ID(str(sub_modulo.modulo_sistema_id)),
            estado_id=strawberry.ID(str(sub_modulo.estado_id)),
            funcionalidades=funcionalidades,
        )
