import { useTranslation } from "react-i18next";

import {
  nombreCompleto,
  type Entidad,
} from "@/modules/entidades/types/entidad.types";
import { Badge } from "@/shared/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";


export function Dato({
  etiqueta,
  children,
}: {
  etiqueta: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-0.5">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">
        {etiqueta}
      </p>
      <p className="text-sm">{children || "—"}</p>
    </div>
  );
}

export function DatosGenerales({ entidad }: { entidad: Entidad }) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>{nombreCompleto(entidad)}</CardTitle>
        {entidad.estado && (
          <Badge variant="secondary">{entidad.estado.nombre}</Badge>
        )}
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
