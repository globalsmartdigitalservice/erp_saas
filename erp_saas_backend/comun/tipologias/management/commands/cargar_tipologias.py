"""
Semilla de `tipologia` — el catálogo del sistema.

Carga DOS cosas por lista: su CABECERA —la fila `indice = 0`, que guarda
el nombre que ve la gente— y sus VALORES, del 1 en adelante. Cada
valor puede traer su `abreviatura`, la forma corta para tickets.

Es la PRIMERA que hay que correr: `Pais.estado`, `Moneda.estado` y los
tres campos de `Empresa` (tipo, rubro, estado) son FK obligatorias acá.
Sin estas filas no se puede insertar nada en ninguna otra tabla.

Todas nacen con `empresa = NULL` = catálogo del sistema, igual para
todas las empresas. Lo que cada cliente agregue después lleva su propio
empresa_id y solo lo ve él.

 **Sin esta semilla el sistema no tiene los nombres de sus listas**:
`api.agrupadores()` devuelve vacío y la pantalla de configuración
arranca en blanco. Por eso `cargar_semillas` va en el arranque, no es
un paso opcional del primer despliegue.

Idempotente: `get_or_create` contra la constraint única
(empresa, agrupador, nombre). Correrlo diez veces deja las mismas filas.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from comun.tipologias.constantes import (
    ABREV_ESTADO_ACTIVO,
    ABREV_ESTADO_BAJA,
    AGRUPADOR,
    INDICE_CABECERA,
    NOMBRE_ESTADO_ACTIVO,
    NOMBRE_ESTADO_BAJA,
    NOMBRE_ACCESO_BLOQUEADO,
    NOMBRE_ACCESO_EXITO,
    NOMBRE_ACCESO_FALLO,
    NOMBRE_EXCEPCION_BLOQUEO,
    NOMBRE_EXCEPCION_PERMISO,
)
from comun.tipologias.models import Tipologia
from core.tenancy import sin_filtro_de_empresa

# Cada entrada es:
#
#     agrupador: ("NOMBRE DE LA LISTA", [(valor, abreviatura), ...])
#
# La abreviatura es la "forma corta para columnas estrechas, tickets e
# impresiones" (modelo de datos). Va vacía donde no tiene sentido: no se
# inventa una para cada valor.
#
# El NOMBRE se carga como CABECERA —la fila con `indice = 0`— y los
# valores van del 1 en adelante, en el orden en que aparecen acá: ése es
# el orden del combo.
#
# El nombre de la lista vive ACÁ y no en `constantes.py`. En el
# código la lista se nombra por su constante (`AGRUPADOR.RUBRO`), que no
# cambia nunca; lo que se le muestra a la gente es este texto, y el
# proveedor lo puede editar en la base sin redesplegar.
#
# EN MAYÚSCULAS: es la convención del catálogo de fábrica, y sale de la
# muestra de datos del análisis funcional. Aplica a lo que
# siembra el proveedor; lo que cargue cada cliente lo escribe como quiera.
#
# CÓMO AGREGAR: se suma el nombre a la lista que corresponde, o un
# agrupador nuevo (que primero hay que declarar en constantes.py, y que
# necesita SÍ o SÍ su nombre acá: hay un test que lo verifica).
# Al redeployar, get_or_create inserta solo lo nuevo.
CATALOGO = {
    # ─── Módulo 11 · Core / Multiempresa ───
    #
    # UNA sola lista para el alta/baja de todos los catálogos: país,
    # ubicación, moneda y las ~180 que vienen. Antes eran tres listas con
    # exactamente los mismos dos valores.
    #
    # El nombre de la lista y las abreviaturas salen de su muestra.
    AGRUPADOR.ESTADO_REGISTRO: (
        "ESTADOS GENERALES",
        [
            (NOMBRE_ESTADO_ACTIVO, ABREV_ESTADO_ACTIVO),
            (NOMBRE_ESTADO_BAJA, ABREV_ESTADO_BAJA),
        ],
    ),
    # Los ocho rubros salen de la muestra de datos del análisis funcional,
    # en su orden: dice INDUSTRIA donde antes decía "Manufactura", y suma
    # SALUD, EDUCACIÓN y TRANSPORTE.
    #
    # (En su muestra CONSTRUCCIÓN aparece dos veces, en los índices 6 y 16.
    # Acá va una sola: la constraint única (empresa, agrupador, nombre)
    # rechazaría la segunda.)
    AGRUPADOR.RUBRO: (
        "RUBRO O SECTOR",
        [
            ("COMERCIO", ""),
            ("SERVICIOS", ""),
            ("SALUD", ""),
            ("EDUCACIÓN", ""),
            ("INDUSTRIA", ""),
            ("CONSTRUCCIÓN", ""),
            ("AGROPECUARIO", ""),
            ("TRANSPORTE", ""),
        ],
    ),
    # OJO: NO son figuras legales (S.A., S.R.L.). Es la POSICIÓN de la
    # empresa dentro del grupo. El modelo de datos lo dice explícito:
    # "Clasifica el registro dentro de la jerarquía (casa matriz,
    # sucursal, filial…)".
    #
    # La figura legal no tiene campo propio: viaja dentro de
    # `razon_social` ("Ferretería El Tornillo S.A."), que es la
    # denominación registrada ante el fisco.
    AGRUPADOR.TIPO_EMPRESA: (
        "TIPOS DE EMPRESA",
        [
            ("CASA MATRIZ", ""),
            ("SUCURSAL", ""),
            ("FILIAL", ""),
        ],
    ),
    # `Empresa` conserva la suya: "SUSPENDIDA" no es ni alta ni baja.
    AGRUPADOR.ESTADO_EMPRESA: (
        "ESTADOS DE EMPRESA",
        [
            ("ACTIVA", ""),
            ("INACTIVA", ""),
            ("SUSPENDIDA", ""),
        ],
    ),
    # ─── Módulo 04 · Entidades / Terceros ───
    #
    # DE LOS CUATRO, SOLO LOS VALORES DE `TIPO_ROL` TIENEN FUENTE.
    # Salen textuales de la descripción del módulo 04 en el modelo de datos
    # El modelo de datos: "Cliente, Proveedor, Paciente, Socio son ROLES de la misma
    # Entidad". Los otros tres NO están en ninguna fuente — son una
    # PROPUESTA para que las listas no nazcan vacías, porque los tres
    # `tipoXId` son FK obligatorias y sin valores no se puede dar de alta
    # ni una entidad.
    #
    # Cambiarlos es barato mientras no haya datos: se edita este archivo.
    # Lo que NO se puede cambiar después es el NÚMERO del agrupador.
    AGRUPADOR.TIPO_ENTIDAD: (
        "TIPOS DE ENTIDAD",
        [
            ("PERSONA NATURAL", "NAT"),
            ("PERSONA JURÍDICA", "JUR"),
        ],
    ),
    # Los documentos de identidad y tributarios que se usan en Bolivia.
    # El sistema es multipaís: cuando entre el segundo país, esta
    # lista la AMPLÍA cada cliente con lo suyo — para eso existe
    # `empresa_agrupador`, que es exactamente este caso de uso.
    AGRUPADOR.TIPO_DOCUMENTO: (
        "TIPOS DE DOCUMENTO",
        [
            ("CÉDULA DE IDENTIDAD", "CI"),
            ("NIT", "NIT"),
            ("PASAPORTE", "PAS"),
            ("CARNET DE EXTRANJERÍA", "CEX"),
        ],
    ),
    # ÚNICOS CON FUENTE: la descripción del módulo 04, textual.
    AGRUPADOR.TIPO_ROL: (
        "TIPOS DE ROL",
        [
            ("CLIENTE", "CLI"),
            ("PROVEEDOR", "PRO"),
            ("PACIENTE", "PAC"),
            ("SOCIO", "SOC"),
        ],
    ),
    AGRUPADOR.TIPO_DIRECCION: (
        "TIPOS DE DIRECCIÓN",
        [
            ("DOMICILIO", "DOM"),
            ("FACTURACIÓN", "FACT"),
            ("ENTREGA", "ENT"),
        ],
    ),
    # ─── Módulo 17 · Servicios de Plataforma ───
    #
    # ESTOS VALORES SÍ TIENEN FUENTE: salen de la descripción de
    # `Referencia_Cruzada.tipoVinculoId` en el modelo de datos — "Semántica del
    # vínculo (genera, respalda, deriva-de…)". El "…" del modelo de datos
    # sugiere que hay más; se agregan cuando aparezcan los casos.
    AGRUPADOR.TIPO_VINCULO: (
        "TIPOS DE VÍNCULO",
        [
            ("GENERA", "GEN"),
            ("RESPALDA", "RESP"),
            ("DERIVA DE", "DER"),
        ],
    ),
    # ─── Módulo 12 · Usuarios y Seguridad ───
    #
    # ESTOS DOS NO SON DECORATIVOS: sin ellos, dos tablas del módulo 12
    # NO SE PUEDEN USAR. `Dispositivo.tipo` y `Horario_Excepcion.tipo` son
    # FK obligatorias, así que sin estas filas el alta falla.
    #
    # Los dos campos eran String suelto en el modelo de datos, marcados M6 ("migrar a
    # tipoId  Tipologia"). Se convirtieron.
    AGRUPADOR.TIPO_DISPOSITIVO: (
        "TIPOS DE DISPOSITIVO",
        [
            # SIN FUENTE: el modelo de datos dice "String" y nada más. Estos
            # cuatro salen de lo que se ve en una empresa boliviana chica;
            # se agregan más cuando aparezcan los casos.
            ("PC DE ESCRITORIO", "PC"),
            ("NOTEBOOK", "NB"),
            ("TABLET", "TAB"),
            ("PUNTO DE VENTA", "POS"),
        ],
    ),
    # EL MÁS DELICADO DE TODA LA SEMILLA.
    #
    # De este valor depende que una excepción de horario DEJE ENTRAR o
    # IMPIDA ENTRAR — lo contrario una de la otra.
    #
    # Los nombres NO se escriben acá a mano: salen de las constantes,
    # porque `dominios/seguridad/services/acceso.py` los compara POR
    # NOMBRE. Un literal desincronizado no daría error: haría que la
    # excepción no coincida con ninguno de los dos y se ignore en
    # silencio — o sea, el bloqueo de unas vacaciones dejaría entrar.
    AGRUPADOR.TIPO_EXCEPCION_HORARIO: (
        "TIPOS DE EXCEPCIÓN DE HORARIO",
        [
            (NOMBRE_EXCEPCION_PERMISO, "PERM"),
            (NOMBRE_EXCEPCION_BLOQUEO, "BLOQ"),
        ],
    ),
    # El desenlace de cada ingreso, para `Sesion_Acceso`. Los nombres
    # salen de constantes por lo mismo que arriba: el service de login los
    # busca POR NOMBRE.
    #
    # FALLO se siembra pero HOY NO SE USA: un fallo de contraseña pasa
    # antes de elegir empresa, y esa tabla es tenant. Va al log técnico
    # ahora y a la tabla del proveedor del módulo 16 cuando exista. Se
    # deja sembrado para no tener que renumerar el
    # día que se registre.
    AGRUPADOR.RESULTADO_ACCESO: (
        "RESULTADOS DE ACCESO",
        [
            (NOMBRE_ACCESO_EXITO, "OK"),
            (NOMBRE_ACCESO_BLOQUEADO, "BLOQ"),
            (NOMBRE_ACCESO_FALLO, "FALL"),
        ],
    ),
    # Los cuatro regímenes de Bolivia. El campo de `Entidad` es opcional:
    # un cliente del exterior no tributa en ninguno de estos.
    AGRUPADOR.REGIMEN_TRIBUTARIO: (
        "REGÍMENES TRIBUTARIOS",
        [
            ("RÉGIMEN GENERAL", "RG"),
            ("RÉGIMEN TRIBUTARIO SIMPLIFICADO", "RTS"),
            ("SISTEMA TRIBUTARIO INTEGRADO", "STI"),
            ("RÉGIMEN AGROPECUARIO UNIFICADO", "RAU"),
        ],
    ),
}


class Command(BaseCommand):
    help = "Carga las tipologías del sistema (empresa = NULL). Idempotente."

    @transaction.atomic
    def handle(self, *args, **options):
        nuevas = 0
        total = 0

        # Puerta de salida explícita: esto cruza empresas a propósito.
        # Y hace falta doblemente acá: sin ella `.valores()` escondería
        # las cabeceras que se acaban de crear.
        with sin_filtro_de_empresa():
            for agrupador, (nombre_lista, valores) in CATALOGO.items():
                # La cabecera primero: es el nombre de la lista. Va sin
                # abreviatura — no es un valor que se muestre en un ticket.
                filas = [(INDICE_CABECERA, nombre_lista, "")]
                filas += [
                    (indice, nombre, abreviatura)
                    for indice, (nombre, abreviatura) in enumerate(valores, start=1)
                ]

                for indice, nombre, abreviatura in filas:
                    _, creada = Tipologia.objects.get_or_create(
                        empresa=None,
                        agrupador=agrupador,
                        nombre=nombre,
                        defaults={
                            "indice": indice,
                            "abreviatura": abreviatura,
                        },
                    )
                    total += 1
                    nuevas += creada

        self.stdout.write(
            self.style.SUCCESS(
                f"tipologías: {total} esperadas, {nuevas} creadas, "
                f"{total - nuevas} ya estaban."
            )
        )
