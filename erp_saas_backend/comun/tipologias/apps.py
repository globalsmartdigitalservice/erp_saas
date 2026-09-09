from django.apps import AppConfig


class TipologiasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # Ruta completa: la app vive dentro del paquete de agrupación comun/.
    name = "comun.tipologias"
    # Sin esto, Django usaría "tipologias" igual, pero se declara
    # explícito porque con ~40 apps puede haber nombres cortos repetidos.
    label = "tipologias"
    verbose_name = "Tipologías"
