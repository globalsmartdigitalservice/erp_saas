"""
Orquestador: corre las cuatro semillas en el orden correcto.

    python manage.py cargar_semillas

Vive en `tipologias` porque es la raíz de la cadena de dependencias.
No importa nada de las otras apps: las llama por NOMBRE con
`call_command`, así que no crea ningún acoplamiento entre apps
hermanas de CAPA 2.

Todo el conjunto es idempotente: se puede correr en cada arranque del
contenedor sin duplicar nada.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand

# El orden importa: monedas y países necesitan que las tipologías
# existan (su `estado` es FK). Idiomas no depende de nadie.
ORDEN = [
    "cargar_tipologias",
    "cargar_idiomas",
    "cargar_monedas",
    "cargar_paises",
]


class Command(BaseCommand):
    help = "Carga TODAS las semillas del sistema, en orden. Idempotente."

    def handle(self, *args, **options):
        for comando in ORDEN:
            self.stdout.write(f"  → {comando}")
            call_command(comando)

        self.stdout.write(self.style.SUCCESS("semillas: listo."))
