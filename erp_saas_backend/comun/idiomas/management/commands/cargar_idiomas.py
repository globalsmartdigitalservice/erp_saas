"""
Semilla de `idioma`.

No depende de nada: `Idioma` no tiene ninguna FK. Se puede correr
antes o después de las tipologías, da igual.

Hace falta porque `Empresa.idioma_default` es FK obligatoria.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from comun.idiomas.models import Idioma

# (código, nombre)
IDIOMAS = [
    ("es", "Español"),
    ("en", "Inglés"),
]


class Command(BaseCommand):
    help = "Carga los idiomas del sistema. Idempotente."

    @transaction.atomic
    def handle(self, *args, **options):
        nuevos = 0

        for codigo, nombre in IDIOMAS:
            _, creado = Idioma.objects.get_or_create(
                codigo=codigo,
                defaults={"nombre": nombre},
            )
            nuevos += creado

        self.stdout.write(
            self.style.SUCCESS(
                f"idiomas: {len(IDIOMAS)} esperados, {nuevos} creados, "
                f"{len(IDIOMAS) - nuevos} ya estaban."
            )
        )
