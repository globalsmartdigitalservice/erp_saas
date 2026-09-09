from django.apps import AppConfig


class NumeracionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "servicios.numeracion"
    label = "numeracion"
    verbose_name = "Numeración de documentos"
