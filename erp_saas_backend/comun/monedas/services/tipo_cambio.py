import datetime

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.monedas.models import Moneda, TipoCambio
from comun.monedas.repository import moneda as repo_moneda
from comun.monedas.repository import tipo_cambio as repo
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ESTADO_ACTIVO,
    NOMBRE_ESTADO_BAJA,
)
from core.tenancy import empresa_actual


def _empresa_del_contexto() -> int:
    """
    INVARIANTE 5 — la empresa sale del contexto, nunca del input.

    `ModeloTenant` la rellenaría igual al guardar, pero si no hay
    contexto la dejaría en None y la base contestaría con un
    IntegrityError sin explicación. Acá se falla antes y con un motivo.
    """
    empresa_id = empresa_actual()
    if empresa_id is None:
        raise ValidationError(
            "No hay empresa en el contexto. Una cotización es de una empresa: "
            "sin saber cuál, no se puede cargar."
        )
    return empresa_id


def _estado(nombre: str):
    """
    La fila de estado que la semilla garantiza, de la lista compartida.

    No se le pide al que llama: una cotización nace activa y se anula,
    no hay una tercera opción que elegir. Lo que el sistema decide no
    va en el input.
    """
    fila = tipologias.obtener_del_sistema(AGRUPADOR.ESTADO_REGISTRO, nombre)
    if fila is None:
        raise ValidationError(
            f"Falta la tipología '{nombre}' del agrupador ESTADO_REGISTRO. "
            f"Ejecute: python manage.py cargar_semillas"
        )
    return fila


def _obtener_moneda_o_fallar(moneda_id: int, papel: str) -> Moneda:
    moneda = repo_moneda.obtener(moneda_id)
    if moneda is None:
        raise ValidationError(f"No existe la moneda {papel} {moneda_id}.")
    return moneda


def _validar_valor(valor) -> None:
    """
    INVARIANTE 1 — la cotización es un número positivo.

    Un 0 deja todos los montos convertidos en cero (o revienta al
    dividir); un negativo da importes negativos que nadie mira hasta el
    cierre.
    """
    if valor is None or valor <= 0:
        raise ValidationError(
            f"La cotización tiene que ser mayor a cero. Recibido: {valor}."
        )


def _validar_par(origen: Moneda, destino: Moneda) -> None:
    """
    INVARIANTE 2 — una moneda no se cotiza contra sí misma.

    Si existiera la fila `BOB → BOB · 6.96`, cada importe en bolivianos
    se multiplicaría por 6.96 y TODOS los `montoBase` quedarían mal, en
    silencio. La base también lo impide (hay CheckConstraint), pero acá
    el mensaje se entiende.
    """
    if origen.pk == destino.pk:
        raise ValidationError(
            f"'{origen.codigo}' no se cotiza contra sí misma: vale 1. Una "
            f"cotización va siempre de una moneda a OTRA."
        )


@transaction.atomic
def registrar(
    *,
    moneda_origen_id: int,
    moneda_destino_id: int,
    fecha: datetime.date,
    valor,
) -> TipoCambio:
    """
    Carga la cotización de un par para una fecha, EN LA EMPRESA ACTIVA.

    No hay parámetro `empresa_id` y no lo va a haber: si el cliente
    pudiera mandarlo, cargaría cotizaciones en la empresa de otro
    (mass assignment).
    """
    _empresa_del_contexto()
    origen = _obtener_moneda_o_fallar(moneda_origen_id, "de origen")
    destino = _obtener_moneda_o_fallar(moneda_destino_id, "de destino")
    _validar_par(origen, destino)
    _validar_valor(valor)

    if repo.existe(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        fecha=fecha,
    ):
        raise ValidationError(
            f"Ya hay una cotización de {origen.codigo} a {destino.codigo} para "
            f"el {fecha}. Si el valor está mal, corregila en vez de cargar otra. "
            f"(Una anulada también ocupa el lugar: la fila no se borra.)"
        )

    return repo.crear(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        fecha=fecha,
        valor=valor,
        estado_id=_estado(NOMBRE_ESTADO_ACTIVO).pk,
    )


def vigente(
    *, moneda_origen_id: int, moneda_destino_id: int, fecha: datetime.date
) -> TipoCambio | None:
    """La que rige en esa fecha para la empresa activa. Ignora las anuladas."""
    return repo.obtener_vigente(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        fecha=fecha,
        estado_id=_estado(NOMBRE_ESTADO_ACTIVO).pk,
    )


def historial(
    *,
    moneda_origen_id: int,
    moneda_destino_id: int,
    desde: datetime.date | None = None,
    hasta: datetime.date | None = None,
    incluir_anuladas: bool = False,
) -> list[TipoCambio]:
    estado_id = None if incluir_anuladas else _estado(NOMBRE_ESTADO_ACTIVO).pk
    return repo.listar(
        moneda_origen_id=moneda_origen_id,
        moneda_destino_id=moneda_destino_id,
        desde=desde,
        hasta=hasta,
        estado_id=estado_id,
    )


def _obtener_o_fallar(tipo_cambio_id: int) -> TipoCambio:
    cotizacion = repo.obtener(tipo_cambio_id)
    if cotizacion is None:
        # También cae acá la cotización de OTRA empresa: el manager de
        # ModeloTenant no la devuelve. El mensaje no distingue los dos
        # casos a propósito.
        raise ValidationError(f"No existe la cotización {tipo_cambio_id}.")
    return cotizacion


@transaction.atomic
def corregir(tipo_cambio_id: int, valor) -> TipoCambio:
    """
    Cambia el VALOR de una cotización ya cargada. Para el dedazo.

    No reescribe historia: las facturas ya emitidas guardan su propia
    tasa congelada.

    Las monedas y la fecha NO se pueden cambiar — no son parámetros.
    Moverlas es, en los hechos, anular esta cotización y cargar otra;
    que se haga explícito.
    """
    cotizacion = _obtener_o_fallar(tipo_cambio_id)
    _validar_valor(valor)

    return repo.actualizar(cotizacion, valor=valor)


@transaction.atomic
def anular(tipo_cambio_id: int) -> TipoCambio:
    """
    Soft delete: la fila no tendría que existir.

    Es lo que el modelo de datos agregó con `estadoId`. Deja de ofrecerse como
    sugerencia, pero la fila queda: si un documento la usó, su
    `tipoCambioId` sigue apuntando a algo y la auditoría no se rompe.
    """
    cotizacion = _obtener_o_fallar(tipo_cambio_id)

    return repo.actualizar(cotizacion, estado=_estado(NOMBRE_ESTADO_BAJA))
