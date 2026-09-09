"""Las mutations de monedas."""

import decimal

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from dominios.seguridad.permisos import auto_permisos

from comun.monedas import api as monedas
from comun.tipologias import api as tipologias
from comun.tipologias.graphql.types import TipologiaType

from .inputs import ActualizarMonedaInput, CrearMonedaInput, RegistrarCotizacionInput
from .types import MonedaType, TipoCambioType


def _a_moneda(fila) -> MonedaType:
    tipologia = tipologias.obtener_varias([fila.estado_id]).get(fila.estado_id)
    estado = TipologiaType.desde_modelo(tipologia) if tipologia else None
    return MonedaType.desde_modelo(fila, estado)


def _traducir(error: ValidationError) -> GraphQLError:
    """
    Un `ValidationError` del dominio es un error ESPERADO: el mensaje va
    tal cual al cliente. Cualquier otra excepción sube sin tocar, para
    que no se disfrace un bug de error de validación.
    """
    return GraphQLError("; ".join(error.messages))


@auto_permisos(recurso="CORE_MONEDAS")
@strawberry.type
class MonedaMutations:
    @strawberry.mutation(description="Crea una moneda. Catálogo del sistema.")
    def crear_moneda(self, datos: CrearMonedaInput) -> MonedaType:
        try:
            fila = monedas.crear_moneda(
                descripcion=datos.descripcion,
                codigo=datos.codigo,
                simbolo=datos.simbolo,
                estado_id=int(datos.estado_id),
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_moneda(fila)

    @strawberry.mutation(
        description="Cambia los datos de una moneda del catálogo. Qué "
        "empresa la usa como base no se decide acá."
    )
    def actualizar_moneda(
        self, id: strawberry.ID, datos: ActualizarMonedaInput
    ) -> MonedaType:
        campos = {
            campo: valor
            for campo, valor in (
                ("descripcion", datos.descripcion),
                ("codigo", datos.codigo),
                ("simbolo", datos.simbolo),
                (
                    "estado_id",
                    int(datos.estado_id) if datos.estado_id is not None else None,
                ),
            )
            if valor is not None
        }
        try:
            fila = monedas.actualizar_moneda(int(id), **campos)
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_moneda(fila)

    @strawberry.mutation(
        description="Saca una moneda del catálogo. Soft delete: la fila "
        "queda, se le pone el estado Baja. Rechaza las que alguna empresa "
        "esté usando."
    )
    def desactivar_moneda(self, id: strawberry.ID) -> MonedaType:
        try:
            fila = monedas.desactivar_moneda(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return _a_moneda(fila)


@auto_permisos(recurso="CORE_COTIZACIONES")
@strawberry.type
class CotizacionMutations:
    @strawberry.mutation(
        description="Carga la cotización de un par de monedas para una "
        "fecha, en la empresa activa. Una moneda no se cotiza contra sí "
        "misma: vale 1."
    )
    def registrar_cotizacion(self, datos: RegistrarCotizacionInput) -> TipoCambioType:
        try:
            fila = monedas.registrar_cotizacion(
                moneda_origen_id=int(datos.moneda_origen_id),
                moneda_destino_id=int(datos.moneda_destino_id),
                fecha=datos.fecha,
                valor=datos.valor,
            )
        except ValidationError as error:
            raise _traducir(error) from error
        return TipoCambioType.desde_modelo(fila)

    @strawberry.mutation(
        description="Corrige el VALOR de una cotización mal cargada (el "
        "dedazo: 69.6 por 6.96). No reescribe documentos: cada uno guarda "
        "su tasa congelada."
    )
    def corregir_cotizacion(
        self, id: strawberry.ID, valor: decimal.Decimal
    ) -> TipoCambioType:
        try:
            fila = monedas.corregir_cotizacion(int(id), valor)
        except ValidationError as error:
            raise _traducir(error) from error
        return TipoCambioType.desde_modelo(fila)

    @strawberry.mutation(
        description="Anula una cotización que no tendría que existir (fecha "
        "equivocada, cargada dos veces). Soft delete: deja de sugerirse pero "
        "la fila queda, así los documentos que la usaron siguen auditables."
    )
    def anular_cotizacion(self, id: strawberry.ID) -> TipoCambioType:
        try:
            fila = monedas.anular_cotizacion(int(id))
        except ValidationError as error:
            raise _traducir(error) from error
        return TipoCambioType.desde_modelo(fila)


@strawberry.type
class MonedaMutation(MonedaMutations, CotizacionMutations):
    """La superficie de escritura de monedas. Solo compone."""
