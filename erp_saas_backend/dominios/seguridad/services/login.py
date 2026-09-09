import datetime

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import transaction

from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import (
    AGRUPADOR,
    NOMBRE_ACCESO_BLOQUEADO,
    NOMBRE_ACCESO_EXITO,
    NOMBRE_ESTADO_ACTIVO,
)
from core.red import ip_del_cliente, user_agent_de
from core.tenancy import empresa as contexto_empresa
from core.tenancy import sin_filtro_de_empresa
from dominios.seguridad import tokens
from dominios.seguridad.models import SesionAcceso
from dominios.seguridad.services import acceso as svc_acceso

# El mismo texto para todos los fallos de credenciales. Ver el docstring.
CREDENCIALES_INVALIDAS = "Usuario o contraseña incorrectos."


class Ingreso:
    """Lo que devuelve un login exitoso.

    `empresas` viene lleno solo cuando la persona trabaja en más de una y
    todavía no eligió."""

    def __init__(self, *, usuario, acceso="", refresh="", sesion=None, empresas=None):
        self.usuario = usuario
        self.acceso = acceso
        self.refresh = refresh
        self.sesion = sesion
        self.empresas = empresas or []

    @property
    def necesita_elegir_empresa(self) -> bool:
        return not self.acceso and bool(self.empresas)


def _tipologia(agrupador, nombre):
    return tipologias.obtener_del_sistema(agrupador, nombre)


def _estado_activo():
    valor = _tipologia(AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO)
    if valor is None:
        raise ValidationError(
            "Falta la tipología 'ACTIVO'. Corré: python manage.py cargar_semillas"
        )
    return valor


def _resultado(nombre):
    valor = _tipologia(AGRUPADOR.RESULTADO_ACCESO, nombre)
    if valor is None:
        raise ValidationError(
            f"Falta la tipología '{nombre}' del agrupador RESULTADO_ACCESO. "
            f"Corré: python manage.py cargar_semillas"
        )
    return valor


def autenticar(*, identificador: str, password: str):
    """Paso 1. Acepta nombre de usuario o correo. El backend iguala el
    tiempo de respuesta exista o no la persona."""
    usuario = authenticate(request=None, username=identificador, password=password)
    if usuario is None:
        # El fallo no se registra en `Sesion_Acceso`: ocurre antes de
        # elegir empresa y esa tabla necesita una. Va al log técnico hasta
        # que exista la tabla de accesos del proveedor.
        raise ValidationError(CREDENCIALES_INVALIDAS)
    return usuario


def empresas_de(usuario) -> list:
    """Paso 2. Cruza empresas a propósito: todavía no hay empresa en el
    contexto, es justo la que se está averiguando."""
    activo = _estado_activo()
    return [
        m
        for m in membresias.empresas_de(usuario.pk)
        if m.estado_id == activo.pk
    ]


# SIN `@transaction.atomic`, y es deliberado: un acceso rechazado escribe
# su registro y después levanta. Con la función entera en una transacción,
# el `raise` haría rollback y se llevaría puesto ese registro.
def ingresar(
    *,
    identificador: str,
    password: str,
    empresa_id: int | None = None,
    request=None,
    mac: str | None = None,
    momento: datetime.datetime | None = None,
) -> Ingreso:
    """El login completo.

    Sin `empresa_id`: si trabaja en una entra directo, si trabaja en varias
    devuelve la lista sin token. Con `empresa_id` entra a esa, si es suya.
    """
    usuario = autenticar(identificador=identificador, password=password)

    disponibles = empresas_de(usuario)
    if not disponibles:
        # Se autenticó pero no trabaja en ninguna empresa activa. El
        # mensaje SÍ puede ser específico: ya demostró quién es, y este
        # caso lo resuelve un administrador, no la persona.
        raise ValidationError(
            "Tu usuario no está habilitado en ninguna empresa. Hablá con el "
            "administrador."
        )

    if empresa_id is None:
        if len(disponibles) > 1:
            return Ingreso(usuario=usuario, empresas=disponibles)
        elegida = disponibles[0]
    else:
        elegida = next(
            (m for m in disponibles if m.empresa_id == empresa_id), None
        )
        if elegida is None:
            # Mismo mensaje que si la empresa no existiera: probando ids
            # no se averigua cuáles hay.
            raise ValidationError("Esa empresa no está disponible para tu usuario.")

    return _abrir_sesion(
        usuario=usuario,
        membresia=elegida,
        request=request,
        mac=mac,
        momento=momento,
    )


def _abrir_sesion(*, usuario, membresia, request, mac, momento) -> Ingreso:
    """Pasos 3, 4 y 5: verificar el acceso, registrarlo y emitir los tokens."""
    ip = ip_del_cliente(request)

    with contexto_empresa(membresia.empresa_id):
        veredicto = svc_acceso.puede_entrar(
            membresia_id=membresia.pk,
            momento=momento,
            mac=mac,
            ip_publica=ip,
        )

        if not veredicto:
            # `atomic` acá adentro y no afuera: este registro queda
            # commiteado por su cuenta y el `raise` de abajo no se lo lleva.
            # `fin` se pone en el acto: una sesión bloqueada nunca estuvo
            # abierta.
            with transaction.atomic():
                SesionAcceso.objects.create(
                    usuario=usuario,
                    resultado=_resultado(NOMBRE_ACCESO_BLOQUEADO),
                    ip=ip,
                    user_agent=user_agent_de(request),
                    estado=_estado_activo(),
                    fin=datetime.datetime.now(datetime.UTC),
                )
            # El mensaje SÍ es específico: ya se autenticó, así que
            # decirle por qué no puede entrar le ahorra un llamado.
            raise ValidationError(veredicto.motivo)

        with transaction.atomic():
            sesion = SesionAcceso.objects.create(
                usuario=usuario,
                resultado=_resultado(NOMBRE_ACCESO_EXITO),
                ip=ip,
                user_agent=user_agent_de(request),
                estado=_estado_activo(),
                fin=None,
            )

        acceso = tokens.emitir_acceso(
            usuario_id=usuario.pk,
            empresa_id=membresia.empresa_id,
            sesion_id=sesion.pk,
        )
        refresh, jti = tokens.emitir_refresh(
            usuario_id=usuario.pk,
            empresa_id=membresia.empresa_id,
            sesion_id=sesion.pk,
        )
        sesion.refresh_jti = jti
        sesion.save(update_fields=["refresh_jti"])

    return Ingreso(
        usuario=usuario, acceso=acceso, refresh=refresh, sesion=sesion
    )


# Sin `@transaction.atomic` por lo mismo que `ingresar`: delega en él.
def elegir_empresa(
    *,
    identificador: str,
    password: str,
    empresa_id: int,
    request=None,
    mac: str | None = None,
    momento: datetime.datetime | None = None,
) -> Ingreso:
    """El segundo paso del login cuando había varias empresas.

     Se piden las credenciales OTRA VEZ: entre la lista y la elección no se
    emitió ningún token, así que no hay nada que demuestre quién es. Un token
    intermedio sería otra credencial más para cuidar."""
    return ingresar(
        identificador=identificador,
        password=password,
        empresa_id=empresa_id,
        request=request,
        mac=mac,
        momento=momento,
    )


@transaction.atomic
def renovar(*, refresh: str) -> Ingreso:
    """Cambia un refresh válido por un par nuevo, con rotación.

    Compara el `jti`: si no coincide, ese refresh ya fue usado — o se lo
    robaron, o hay dos clientes con el mismo. En los dos casos no se renueva."""
    try:
        datos = tokens.leer(refresh, tipo=tokens.TIPO_REFRESH)
    except tokens.TokenInvalido as error:
        raise ValidationError("La sesión venció. Volvé a entrar.") from error

    with sin_filtro_de_empresa():
        # Sin filtro porque todavía no hay empresa en el contexto: se está
        # justamente por ponerla, con lo que diga el token.
        sesion = SesionAcceso.objects.filter(pk=datos["ses"]).first()

    if sesion is None or not sesion.esta_abierta:
        raise ValidationError("La sesión venció. Volvé a entrar.")

    if sesion.refresh_jti != datos.get("jti"):
        # Refresh viejo. Ver el aviso del docstring.
        raise ValidationError("La sesión venció. Volvé a entrar.")

    if not sesion.usuario.is_active:
        raise ValidationError("La sesión venció. Volvé a entrar.")

    acceso = tokens.emitir_acceso(
        usuario_id=sesion.usuario_id,
        empresa_id=sesion.empresa_id,
        sesion_id=sesion.pk,
    )
    nuevo_refresh, jti = tokens.emitir_refresh(
        usuario_id=sesion.usuario_id,
        empresa_id=sesion.empresa_id,
        sesion_id=sesion.pk,
    )

    with sin_filtro_de_empresa():
        sesion.refresh_jti = jti
        sesion.save(update_fields=["refresh_jti"])

    return Ingreso(
        usuario=sesion.usuario, acceso=acceso, refresh=nuevo_refresh, sesion=sesion
    )


@transaction.atomic
def salir(*, sesion_id: int) -> SesionAcceso | None:
    """Cierra la sesión: le pone `fin` y borra el `jti`.

     El token de ACCESO sigue valiendo hasta 15 minutos: verificarlo contra
    la base en cada petición costaría una consulta por request. Lo que se
    corta en el acto es la RENOVACIÓN."""
    with sin_filtro_de_empresa():
        sesion = SesionAcceso.objects.filter(pk=sesion_id).first()
        if sesion is None or not sesion.esta_abierta:
            return sesion

        sesion.fin = datetime.datetime.now(datetime.UTC)
        sesion.refresh_jti = ""
        sesion.save(update_fields=["fin", "refresh_jti"])

    return sesion


__all__ = [
    "ingresar",
    "elegir_empresa",
    "renovar",
    "salir",
    "autenticar",
    "empresas_de",
    "Ingreso",
    "CREDENCIALES_INVALIDAS",
]
