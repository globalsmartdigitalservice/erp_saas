import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import {
  nombreCompleto,
  type Entidad,
} from "@/modules/entidades/types/entidad.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import { PageTitle } from "@/shared/components/PageTitle";
import { Card, CardContent, CardHeader } from "@/shared/components/ui/card";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";

export function Dato({
  etiqueta,
  children,
}: {
  etiqueta: string;
  children: ReactNode;
}) {
  return (
    <div className="min-w-0 space-y-0.5">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">
        {etiqueta}
      </p>
      <div className="break-words text-sm">{children || "—"}</div>
    </div>
  );
}

export function DatosGenerales({ entidad }: { entidad: Entidad }) {
  const { t } = useTranslation();
  const activoId = useEstadoActivoId();

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 space-y-0">
        <PageTitle>
          {nombreCompleto(entidad)}
        </PageTitle>
        <BadgeDeEstado estado={entidad.estado} activoId={activoId} />
      </CardHeader>

      <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Dato etiqueta={t("entidades.tipo")}>
          {entidad.tipoEntidad?.nombre}
        </Dato>
        <Dato etiqueta={t("entidades.tipoDocumento")}>
          {entidad.tipoDocumento?.nombre}
        </Dato>
        <Dato etiqueta={t("entidades.documento")}>{entidad.documento}</Dato>
        <Dato etiqueta={t("entidades.regimenTributario")}>
          {entidad.regimenTributario?.nombre}
        </Dato>
      </CardContent>
    </Card>
  );
}
