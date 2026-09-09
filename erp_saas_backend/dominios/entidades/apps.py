from django.apps import AppConfig


class EntidadesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # Ruta completa: la app vive dentro del paquete de agrupación dominios/.
    name = "dominios.entidades"
    # Explícito por la misma razón que en comun/: con ~40 apps los nombres
    # cortos pueden repetirse.
    label = "entidades"
    verbose_name = "Entidades y terceros"
