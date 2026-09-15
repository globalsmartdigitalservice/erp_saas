"""
`python manage.py generar_permisos`

Lee las mutations decoradas con `@auto_permisos` y arma el catálogo:

    · el `auth_permission` que falte
    · la `Funcionalidad` que le pone nombre y pantalla
    · INFORMA los que sobran; con `--borrar-obsoletos` los limpia

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
        parser.add_argument(
            "--borrar-obsoletos",
            action="store_true",
            help=(
                "Borra los permisos que ya no están en el código. Respeta "
                "los que algún rol tenga asignados."
            ),
        )

    def handle(self, *args, **opciones):
        simulacro = opciones["dry_run"]

        declarados = escanear(clases_con_permisos(self.stdout))
        if not declarados:
            self.stdout.write(
                self.style.WARNING(
                    "No se encontró ninguna mutation decorada con @auto_permisos. "
                    "Si esperaba encontrar alguna, revise que la clase esté "
                    "decorada y que su app esté en INSTALLED_APPS."
                )
            )
            return

        duplicados = [d for d in declarados if d["duplicado"]]
        for d in duplicados:
            self.stdout.write(
                self.style.WARNING(
                    f"  aviso: '{d['codename']}' está declarado más de una vez. "
                    f"Se usa el primero ({d['metodo']}); revise si el otro "
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

        self._informar_sobrantes(declarados, opciones["borrar_obsoletos"])

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
                    f"roles van a aparecer como un código suelto. Cree esa "
                    f"pantalla y vuelva a ejecutar el comando."
                )
            )

    def _informar_sobrantes(self, declarados, borrar: bool) -> None:
        """
         NO SE BORRAN SOLOS, Y ES A PROPÓSITO.

        Un permiso que hoy falta del código puede ser un rename a medio
        hacer o una operación que se está reescribiendo, y el catálogo lo
        comparten TODOS los clientes: un borrado automático durante un
        deploy les pega a todos a la vez.

        Con `--borrar-obsoletos` se limpian, salvo los que algún rol tenga
        asignados: ésos son configuración que armó una persona.
        """
        vivos = {d["codename"] for d in declarados}
        sobrantes = list(
            Permission.objects.filter(content_type=content_type_del_ancla())
            .exclude(codename__in=vivos)
            .order_by("codename")
        )
        if not sobrantes:
            return

        with sin_filtro_de_empresa():
            en_uso = set(
                GrupoEmpresaPermiso.objects.filter(
                    auth_permission__in=sobrantes
                ).values_list("auth_permission_id", flat=True)
            )

        if borrar:
            self._borrar_sobrantes(sobrantes, en_uso)
            return

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                f"aviso: {len(sobrantes)} permiso(s) en la base que YA NO están "
                f"en el código. No se borran solos: uno puede ser un rename a "
                f"medio hacer, y el catálogo lo comparten todos los clientes. "
                f"Para limpiarlos: --borrar-obsoletos."
            )
        )
        self._listar(sobrantes, en_uso)

    def _listar(self, sobrantes, en_uso) -> None:
        for permiso in sobrantes:
            marca = " (EN USO por algún rol)" if permiso.pk in en_uso else ""
            self.stdout.write(f"    - {permiso.codename}{marca}")

    def _borrar_sobrantes(self, sobrantes, en_uso) -> None:
        """Los que ningún rol usa. La `Funcionalidad` se va con ellos porque
        es derivada —la creó este comando— y además los tiene con `PROTECT`."""
        borrados, retenidos = [], []

        with transaction.atomic():
            for permiso in sobrantes:
                if permiso.pk in en_uso:
                    retenidos.append(permiso.codename)
                    continue

                funcionalidad = modulos.funcionalidad_del_permiso(permiso.pk)
                if funcionalidad is not None:
                    modulos.borrar_funcionalidad(funcionalidad.pk)

                permiso.delete()
                borrados.append(permiso.codename)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"OK: {len(borrados)} permiso(s) obsoleto(s) borrado(s)."
            )
        )
        for codename in borrados:
            self.stdout.write(f"    - {codename}")

        if not retenidos:
            return

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                f"aviso: {len(retenidos)} no se borraron porque algún rol los "
                f"tiene asignados. Quítelos del rol primero:"
            )
        )
        for codename in retenidos:
            self.stdout.write(f"    - {codename}")

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

        self._informar_sobrantes(declarados, borrar=False)
