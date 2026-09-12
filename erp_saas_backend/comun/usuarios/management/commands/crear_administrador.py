"""Crea el primer usuario del proveedor: el que puede entrar antes que nadie.

    python manage.py crear_administrador

Sale de las mismas variables de entorno que ya entiende `createsuperuser`:
DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL y DJANGO_SUPERUSER_PASSWORD.

Idempotente: corre en cada arranque del contenedor sin romper nada.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Crea el primer usuario del proveedor desde el entorno. Idempotente."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")

    
        if not (password and email):
            self.stdout.write(
                "Faltan DJANGO_SUPERUSER_PASSWORD o DJANGO_SUPERUSER_EMAIL: "
                "no se crea el administrador."
            )
            return

        
        if Usuario.objects.filter(username=username).exists():
            self.stdout.write(f"'{username}' ya existe: no se toca.")
            return

        Usuario.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            debe_cambiar_password=True,
        )
        self.stdout.write(self.style.SUCCESS(f"administrador '{username}' creado."))
