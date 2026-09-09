"""Agrupadores de `Tipologia`: el número de cada lista del sistema.

Se agregan al final con el siguiente número libre, y un valor ya usado
nunca se reutiliza ni se renumera.
"""

from django.db import models

# Los valores de una lista van de 1 en adelante: `indice > 0` es "dame los
# valores, no el título".
INDICE_CABECERA = 0

# Contrato, no etiquetas de pantalla: el código busca estas filas POR
# NOMBRE. Renombrarlas desde el panel del proveedor rompe en silencio el
# soft delete, las excepciones de horario y el registro de accesos.
NOMBRE_ESTADO_ACTIVO = "ACTIVO"
NOMBRE_ESTADO_BAJA = "BAJA"
NOMBRE_EXCEPCION_PERMISO = "PERMISO"
NOMBRE_EXCEPCION_BLOQUEO = "BLOQUEO"
NOMBRE_ACCESO_EXITO = "ÉXITO"
NOMBRE_ACCESO_BLOQUEADO = "BLOQUEADO"
NOMBRE_ACCESO_FALLO = "FALLO"

ABREV_ESTADO_ACTIVO = "A"
ABREV_ESTADO_BAJA = "B"


class AGRUPADOR(models.IntegerChoices):
    """Sin etiquetas: el nombre visible de cada lista vive en su cabecera."""

    # Módulo 11 · Core / Multiempresa
    ESTADO_REGISTRO = 1
    RUBRO = 2
    TIPO_EMPRESA = 3
    ESTADO_EMPRESA = 4

    # Módulo 04 · Entidades
    TIPO_ENTIDAD = 5
    TIPO_DOCUMENTO = 6
    TIPO_ROL = 7
    TIPO_DIRECCION = 8

    # Módulo 17 · Servicios de Plataforma
    TIPO_VINCULO = 9

    # Módulo 12 · Usuarios y Seguridad
    TIPO_DISPOSITIVO = 10
    TIPO_EXCEPCION_HORARIO = 11
    RESULTADO_ACCESO = 12

    # Del módulo 04, pero va al final: el número no se reordena nunca.
    REGIMEN_TRIBUTARIO = 13
