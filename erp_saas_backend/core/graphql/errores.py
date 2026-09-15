"""Qué se le cuenta al cliente cuando algo falla, y qué queda en el log."""

import logging
import uuid

import strawberry
from graphql import GraphQLError
from strawberry.extensions import MaskErrors

logger = logging.getLogger("erp.graphql")

#: Dónde viaja la referencia, del log a la respuesta.
CLAVE_REFERENCIA = "referencia"


def es_esperado(error: GraphQLError) -> bool:
    """
    ¿Este error lo previó el sistema?

    `None`         →  la consulta está mal escrita (sintaxis, campo que
                      no existe). Es un error del que llama, y su mensaje
                      le sirve para arreglarla.
    `GraphQLError` →  lo levantamos nosotros a propósito: es una regla de
                      negocio, con el mensaje ya redactado para el
                      usuario.
    otra cosa      →  se escapó una excepción. Es un bug.
    """
    original = error.original_error
    return original is None or isinstance(original, GraphQLError)


class SchemaDelErp(strawberry.Schema):
    """El schema del proyecto. Lo único que cambia es qué se loguea."""

    def process_errors(self, errors, execution_context=None) -> None:
        for error in errors:
            if es_esperado(error):
                # UNA LÍNEA, SIN TRACEBACK: no es un incidente, es el
                # sistema funcionando. El traceback de una validación
                # esperada solo tapa a los errores de verdad.
                logger.info("Rechazado: %s", error.message)
                continue

            referencia = uuid.uuid4().hex[:12]
            error.extensions[CLAVE_REFERENCIA] = referencia

            # `exc_info` con la excepción ORIGINAL, no con el envoltorio
            # de GraphQL: lo que interesa es dónde se rompió.
            logger.error(
                "Error inesperado [%s]: %s",
                referencia,
                error.message,
                exc_info=error.original_error,
            )


class EnmascararErrores(MaskErrors):
    """
    Lo que ve el cliente de un error inesperado: que ocurrió, y con qué
    referencia pedir ayuda. Nada más.
    """

    def __init__(self) -> None:
        super().__init__(should_mask_error=lambda error: not es_esperado(error))

    def anonymise_error(self, error: GraphQLError) -> GraphQLError:
        referencia = error.extensions.get(CLAVE_REFERENCIA)

        limpio = GraphQLError(
            message=(
                "Ocurrió un error inesperado. Si necesita reportarlo, "
                f"indique la referencia {referencia}."
            ),
            nodes=error.nodes,
            source=error.source,
            positions=error.positions,
            path=error.path,
            # Se corta acá a propósito: con el original encima, cualquiera
            # que lo formatee vuelve a exponer el texto que acabamos de
            # esconder.
            original_error=None,
        )
        # También en `extensions`, para que el frontend pueda mostrarla
        # aparte el día que quiera darle formato propio.
        limpio.extensions[CLAVE_REFERENCIA] = referencia
        return limpio
