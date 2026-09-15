import { useQuery } from "@apollo/client";
import { AlertTriangle, ArrowLeft } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { DatosPersonales } from "@/modules/seguridad/components/miembros/DatosPersonales";
import { MembresiaEnEmpresa } from "@/modules/seguridad/components/miembros/MembresiaEnEmpresa";
import { RolesDeMiembro } from "@/modules/seguridad/components/miembros/RolesDeMiembro";
import { DETALLE_MIEMBRO } from "@/modules/seguridad/graphql/miembros.queries";
import type {
  CuentaDeMiembro,
  MembresiaDeMiembro,
} from "@/modules/seguridad/types/miembro.types";
import { EstadoError } from "@/shared/components/EstadosTabla";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { mensajeDeError } from "@/shared/lib/errores";

export function DetalleMiembroPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const { data, loading, error, refetch } = useQuery<{
    usuario: CuentaDeMiembro | null;
    membresia: MembresiaDeMiembro | null;
  }>(DETALLE_MIEMBRO, { variables: { usuarioId: id }, skip: !id });

  const cuenta = data?.usuario ?? null;
  const membresia = data?.membresia ?? null;

  return (
    <section className="space-y-4">
      <Button asChild variant="ghost" size="sm" className="-ml-2 gap-2">
        <Link to="..">
          <ArrowLeft size={16} />
          {t("miembros.volver")}
        </Link>
      </Button>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <div className="grid gap-4 lg:grid-cols-3">
            <Skeleton className="h-48 lg:col-span-2" />
            <Skeleton className="h-48" />
          </div>
        </div>
      ) : !cuenta || !membresia ? (
        <EstadoError
          icono={AlertTriangle}
          titulo={t("miembros.noExisteFicha")}
          mensaje={mensajeDeError(error, t)}
          onReintentar={() => refetch()}
        />
      ) : (
        <div className="space-y-4 motion-safe:animate-in motion-safe:fade-in">
          <DatosPersonales cuenta={cuenta} />

          <div className="grid items-start gap-4 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <RolesDeMiembro
                membresiaId={membresia.id}
                nombre={cuenta.nombreCompleto || cuenta.username}
              />
            </div>
            <MembresiaEnEmpresa cuenta={cuenta} membresia={membresia} />
          </div>
        </div>
      )}
    </section>
  );
}
