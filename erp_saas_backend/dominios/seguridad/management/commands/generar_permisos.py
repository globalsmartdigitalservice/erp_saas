"""
`python manage.py generar_permisos`

Lee las mutations decoradas con `@auto_permisos` y arma el catálogo:

    · el `auth_permission` que falte
    · la `Funcionalidad` que le pone nombre y pantalla
    · INFORMA los que sobran, y NO los borra

 CON `--dry-run` NO ESCRIBE NADA. Es lo primero que hay que correr:
este comando toca los permisos de todo el sistema, y conviene ver qué va
a hacer antes de que lo haga.
"""

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from comun.catalogo_modulos import api as modulos
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
from dominios.seguridad.permisos import (
    codename_de,
    content_type_del_ancla,
    escanear,
)
from core.tenancy import sin_filtro_de_empresa
from dominios.seguridad.models import GrupoEmpresaPermiso
from dominios.seguridad.scanner import clases_con_permisos


class Command(BaseCommand):
    help = "Arma el catálogo de permisos escaneando las mutations decoradas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué haría, sin escribir nada.",
        )

    def handle(self, *args, **opciones):
        simulacro = opciones["dry_run"]

        declarados = escanear(clases_con_permisos(self.stdout))
        if not declarados:
            self.stdout.write(
                self.style.WARNING(
                    "No se encontró ninguna mutation decorada con @auto_permisos. "
                    "Si esperabas encontrar alguna, revisá que la clase esté "
                    "decorada y que su app esté en INSTALLED_APPS."
                )
            )
            return

        duplicados = [d for d in declarados if d["duplicado"]]
        for d in duplicados:
            self.stdout.write(
                self.style.WARNING(
                    f"  aviso: '{d['codename']}' está declarado más de una vez. "
                    f"Se usa el primero ({d['metodo']}); revisá si el otro "
                    f"quería un `operacion=` distinto."
                )
            )

        self._informar_pantallas_faltantes(declarados)

        if simulacro:
            self._simular(declarados)
            return

        with transaction.atomic():
            nuevos, ya_estaban = self._escribir(declarados)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nOK: {len(nuevos)} permiso(s) nuevo(s), "
                f"{ya_estaban} que ya estaban."
            )
        )
        for codename in nuevos:
            self.stdout.write(f"    + {codename}")

        self._informar_sobrantes(declarados)

    # ── lo que se escribe ──────────────────────────────────────────

    def _escribir(self, declarados) -> tuple[list[str], int]:
        ancla = content_type_del_ancla()
        activo = tipologias.obtener_del_sistema(
            AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
        )

        nuevos, ya_estaban = [], 0

        for d in declarados:
            permiso, creado = Permission.objects.get_or_create(
                content_type=ancla,
                codename=d["codename"],
                defaults={"name": self._etiqueta(d)},
            )
            if creado:
                nuevos.append(d["codename"])
            else:
                ya_estaban += 1

            # La `Funcionalidad` solo se puede crear si su pantalla ya
            # existe. Si no está, se informó más arriba y se saltea: el
            # permiso igual queda creado y usable.
            pantalla = modulos.obtener_sub_modulo_por_codigo(d["recurso"])
            if pantalla is None or activo is None:
                continue
            if modulos.funcionalidad_del_permiso(permiso.pk) is not None:
                continue

            modulos.crear_funcionalidad(
                sub_modulo_id=pantalla.pk,
                auth_permission_id=permiso.pk,
                nombre=self._etiqueta(d),
                descripcion=d["descripcion"],
                estado_id=activo.pk,
            )

        return nuevos, ya_estaban

    @staticmethod
    def _etiqueta(d) -> str:
        """Lo que se lee en la pantalla de armado de roles."""
        return d["descripcion"] or d["operacion"].replace("_", " ").capitalize()

    # ── lo que solo se informa ─────────────────────────────────────

    def _informar_pantallas_faltantes(self, declarados) -> None:
        """
        Un permiso cuyo `recurso` no existe como `Sub_Modulo` se crea
        igual, pero **queda sin Funcionalidad**: o sea sin nombre y sin
        pantalla, así que en el armado de roles aparece como un código
        suelto que nadie sabe qué hace.
        """
        faltantes = sorted(
            {
                d["recurso"]
                for d in declarados
                if modulos.obtener_sub_modulo_por_codigo(d["recurso"]) is None
            }
        )
        for recurso in faltantes:
            self.stdout.write(
                self.style.WARNING(
                    f"  aviso: No existe el Sub_Modulo '{recurso}'. Sus permisos se "
                    f"crean igual, pero sin pantalla ni nombre: en el armado de "
                    f"roles van a aparecer como un código suelto. Creá esa "
                    f"pantalla y volvé a correr el comando."
                )
            )

    def _informar_sobrantes(self, declarados) -> None:
        """
         NO SE BORRAN, Y ES A PROPÓSITO.

        Borrar un `auth_permission` le saca capacidades EN SILENCIO a
        todos los roles que lo tenían asignado: la persona deja de poder
        hacer algo y el mensaje que ve es "no tenés permiso", sin ninguna
        pista. Y además `Grupo_Empresa_Permiso` lo tiene con `PROTECT`,
        así que el borrado fallaría.

        Se listan y decide una persona.
        """
        vivos = {d["codename"] for d in declarados}
        sobrantes = (
            Permission.objects.filter(content_type=content_type_del_ancla())
            .exclude(codename__in=vivos)
            .order_by("codename")
        )
        if not sobrantes:
            return

        self.stdout.write(
            self.style.WARNING(
                f"\naviso: {sobrantes.count()} permiso(s) en la base que YA NO están "
                f"en el código. NO se borran: hacerlo le sacaría capacidades en "
                f"silencio a los roles que los tengan. Revisalos a mano:"
            )
        )

        with sin_filtro_de_empresa():
            en_uso = set(
                GrupoEmpresaPermiso.objects.filter(
                    auth_permission__in=sobrantes
                ).values_list("auth_permission_id", flat=True)
            )

        for permiso in sobrantes:
            marca = " (EN USO por algún rol)" if permiso.pk in en_uso else ""
            self.stdout.write(f"    - {permiso.codename}{marca}")

    def _simular(self, declarados) -> None:
        ancla = content_type_del_ancla()
        existentes = set(
            Permission.objects.filter(content_type=ancla).values_list(
                "codename", flat=True
            )
        )

        self.stdout.write("\nSIMULACRO — no se escribió nada.\n")
        for d in declarados:
            estado = "ya está" if d["codename"] in existentes else "SE CREARÍA"
            self.stdout.write(f"  [{estado}] {d['codename']}  ← {d['metodo']}")

        self._informar_sobrantes(declarados)
