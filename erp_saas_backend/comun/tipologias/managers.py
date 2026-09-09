"""Manager propio: `Tipologia` no puede usar el `TenantManager` normal.

Aquél exige empresa en el contexto y filtra por igualdad exacta. Acá
conviven TRES clases de fila y la empresa activa tiene que ver las tres:

    empresa_id = NULL    catálogo DE FÁBRICA
    empresa_id = 7     →  catálogo de su CASA MATRIZ  ← se hereda
    empresa_id = 12    →  catálogo propio de la SUCURSAL

La regla es que **la configuración baja de la matriz**: si el gimnasio
agrega "Transferencia", las 20 sucursales la ven sin cargar nada. Los
DATOS (ventas, stock) NO se heredan — ésos siguen con filtro exacto.

Y encima va la excepción: `tipologia_oculta` saca de la lista lo que esta
empresa —ella sola, no el grupo— decidió no mostrar.

    WHERE  (empresa_id IN (matriz, propia) OR empresa_id IS NULL)
      AND  NOT EXISTS (oculta para la empresa ACTUAL)
"""

from django.db import models

from comun.tipologias.constantes import INDICE_CABECERA
from core.tenancy import SinEmpresaEnContexto, empresa_actual, filtro_desactivado


class TipologiaQuerySet(models.QuerySet):
    def del_agrupador(self, agrupador):
        return self.filter(agrupador=agrupador)

    def valores(self):
        """
        Los valores de la lista, sin su cabecera. La que se olvida de
        filtrar muestra "Rubros" como si fuera un rubro.
        """
        return self.filter(indice__gt=INDICE_CABECERA)

    def cabeceras(self):
        """Una por lista: la fila que guarda su nombre."""
        return self.filter(indice=INDICE_CABECERA)

    def activas(self):
        return self.filter(estado=self.model.Estado.ACTIVO)

    def del_sistema(self):
        """Solo las globales, sin importar la empresa activa."""
        return self.filter(empresa__isnull=True)


class TipologiaManager(models.Manager.from_queryset(TipologiaQuerySet)):
    def get_queryset(self):
        qs = super().get_queryset()

        if filtro_desactivado():
            return qs

        empresa_id = empresa_actual()
        if empresa_id is None:
            # Sin empresa igual se ven las de fábrica: al dar de alta el
            # primer cliente hay que leer los rubros y todavía no hay
            # empresa en el contexto.
            return qs.filter(empresa__isnull=True)

        # Los imports van acá adentro y no al tope: `empresas.api`
        # importa de vuelta a `tipologias`, y `models` importa este
        # archivo. Al tope el ciclo revienta; acá ya están cargados.
        from comun.empresas import api as empresas
        from comun.tipologias.models import TipologiaOculta

        # Ella y su matriz: 1-2 búsquedas por clave primaria, no crece
        # con la cantidad de clientes.
        ambito = empresas.ids_del_ambito(empresa_id)

        qs = qs.filter(
            models.Q(empresa_id__in=ambito) | models.Q(empresa__isnull=True)
        )

        # El ocultamiento es de LA EMPRESA, no del ámbito: si El Alto se
        # esconde "Tarjeta", la matriz y las otras 19 sucursales la
        # siguen viendo. Por eso acá va `empresa_id`, no `ambito`.
        ocultas = TipologiaOculta.objects.filter(empresa_id=empresa_id).values(
            "tipologia_id"
        )
        return qs.exclude(pk__in=ocultas)


__all__ = ["TipologiaManager", "TipologiaQuerySet", "SinEmpresaEnContexto"]
