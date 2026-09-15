"""Bloquea la sesión con contraseña temporal hasta que la cambie."""

from graphql import (
    ExecutionResult,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLError,
    InlineFragmentNode,
)
from graphql.utilities import get_operation_ast
from strawberry.extensions import SchemaExtension

from dominios.seguridad.permisos_graphql import usuario_de_la_peticion


DEBE_CAMBIAR_PASSWORD = (
    "Por seguridad, debe definir una contraseña nueva para continuar."
)

CODIGO_DEBE_CAMBIAR_PASSWORD = "PASSWORD_CHANGE_REQUIRED"


PERMITIDOS = frozenset(
    {
        "me",
        "miEmpresa",
        "misPermisos",
        "version",
        "cambiarMiPassword",
        "logout",
        "refreshSession",
        "login",
        "elegirEmpresa",
    }
)


class ExigirCambioDePassword(SchemaExtension):
    """Rechaza el documento entero si pide algo fuera de PERMITIDOS."""

    def on_execute(self):
        contexto = self.execution_context

        if _debe_cambiarla(contexto.context) and _campos_raiz(contexto) - PERMITIDOS:
            contexto.result = ExecutionResult(
                data=None,
                errors=[
                    GraphQLError(
                        DEBE_CAMBIAR_PASSWORD,
                        extensions={"code": CODIGO_DEBE_CAMBIAR_PASSWORD},
                    )
                ],
            )

        yield


def _debe_cambiarla(contexto) -> bool:
    usuario = usuario_de_la_peticion(getattr(contexto, "request", None))
    return bool(
        usuario is not None
        and usuario.is_authenticated
        and getattr(usuario, "debe_cambiar_password", False)
    )


def _campos_raiz(contexto) -> set[str]:
    """Los campos raíz de la operación, incluidos los de sus fragmentos."""
    documento = contexto.graphql_document
    operacion = get_operation_ast(documento, contexto.operation_name)
    fragmentos = {
        definicion.name.value: definicion
        for definicion in documento.definitions
        if isinstance(definicion, FragmentDefinitionNode)
    }

    campos = set()
    pendientes = list(operacion.selection_set.selections)
    while pendientes:
        seleccion = pendientes.pop()
        if isinstance(seleccion, FieldNode):
            if not seleccion.name.value.startswith("__"):
                campos.add(seleccion.name.value)
        elif isinstance(seleccion, InlineFragmentNode):
            pendientes.extend(seleccion.selection_set.selections)
        elif isinstance(seleccion, FragmentSpreadNode):
            pendientes.extend(fragmentos[seleccion.name.value].selection_set.selections)
    return campos


__all__ = ["ExigirCambioDePassword", "CODIGO_DEBE_CAMBIAR_PASSWORD"]
