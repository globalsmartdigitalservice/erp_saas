"""Los tipos de membresías que ve el frontend."""

import datetime

import strawberry

from comun.usuarios.graphql.types import UsuarioType


@strawberry.type(name="EmpresaDelUsuario")
class EmpresaDelUsuarioType:
    """
    Una opción del selector "¿dónde querés trabajar?".

    Lleva la razón social ya resuelta porque es lo único que la pantalla
    necesita mostrar: pedirle al frontend que después consulte cada
    empresa por su id sería una consulta por opción.
    """

    membresia_id: strawberry.ID
    empresa_id: strawberry.ID
    razon_social: str
    es_matriz: bool

    @classmethod
    def desde_modelo(cls, membresia) -> "EmpresaDelUsuarioType":
        return cls(
            membresia_id=strawberry.ID(str(membresia.pk)),
            empresa_id=strawberry.ID(str(membresia.empresa_id)),
            razon_social=membresia.empresa.razon_social,
            es_matriz=membresia.empresa.empresa_padre_id is None,
        )


@strawberry.type(name="Membresia")
class MembresiaType:
    """
    Una persona trabajando en una empresa.

    El `usuario` viaja RESUELTO y no como id: la lista de miembros de una
    empresa muestra el nombre de cada uno, y si el frontend tuviera que
    pedirlos de a uno serían N consultas. Quien arma la lista los trae
    por lote con `usuarios.obtener_usuarios()`.
    """

    id: strawberry.ID
    usuario: UsuarioType | None
    fecha_asignacion: datetime.date
    fecha_finalizacion: datetime.date | None
    estado_id: strawberry.ID

    @classmethod
    def desde_modelo(cls, membresia, usuario: UsuarioType | None) -> "MembresiaType":
        return cls(
            id=strawberry.ID(str(membresia.pk)),
            usuario=usuario,
            fecha_asignacion=membresia.fecha_asignacion,
            fecha_finalizacion=membresia.fecha_finalizacion,
            estado_id=strawberry.ID(str(membresia.estado_id)),
        )
