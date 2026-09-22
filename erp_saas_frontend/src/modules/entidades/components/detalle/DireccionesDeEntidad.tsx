import { useMutation } from "@apollo/client";
import { Ban, MapPin } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Dato } from "@/modules/entidades/components/detalle/DatosGenerales";
import { DialogoDireccion } from "@/modules/entidades/components/detalle/DialogoDireccion";
import { DESACTIVAR_DIRECCION } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { Direccion } from "@/modules/entidades/types/entidad.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { EmptyState } from "@/shared/components/TableStates";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader } from "@/shared/components/ui/card";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";

export function DireccionesDeEntidad({
  entidadId,
  direcciones,
}: {
  entidadId: string;
  direcciones: Direccion[];
}) {
  const { t } = useTranslation();
  const activoId = useEstadoActivoId();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-end space-y-0">
        <DialogoDireccion entidadId={entidadId} />
      </CardHeader>

      <CardContent>
        {direcciones.length === 0 ? (
          <EmptyState icon={MapPin} title={t("entidades.sinDirecciones")} />
        ) : (
          <ul className="divide-y">
            {direcciones.map((direccion) => (
              <li
                key={direccion.id}
                className="flex items-start gap-2 py-3 first:pt-0 last:pb-0"
              >
                <div className="min-w-0 flex-1">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <Badge variant="secondary">
                      {direccion.tipo?.nombre ?? "—"}
                    </Badge>
                    <BadgeDeEstado estado={direccion.estado} activoId={activoId} />
                  </div>

                  <div className="grid gap-4 sm:grid-cols-3">
                    <Dato etiqueta={t("entidades.calle")}>
                      {[direccion.calle, direccion.numero]
                        .filter(Boolean)
                        .join(" ")}
                    </Dato>
                    <Dato etiqueta={t("entidades.direccionTexto")}>
                      {direccion.direccionTexto}
                    </Dato>
                    <Dato etiqueta={t("entidades.referencia")}>
                      {direccion.descripcion}
                    </Dato>
                  </div>
                </div>

                <div className="flex shrink-0 items-start">
                  <DialogoDireccion entidadId={entidadId} direccion={direccion} />
                  <BajaDeDireccion direccion={direccion} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function BajaDeDireccion({ direccion }: { direccion: Direccion }) {
  const { t } = useTranslation();

  const [desactivar, mutacion] = useMutation(DESACTIVAR_DIRECCION, {
    refetchQueries: [ENTIDAD],
  });

  return (
    <ConfirmDialog
      title={t("entidades.bajaDireccionTitulo")}
      description={t("entidades.bajaDireccionAyuda")}
      confirmLabel={t("entidades.darDeBaja")}
      mutation={mutacion}
      successMessage={t("entidades.direccionDadaDeBaja")}
      onConfirm={async () => {
        const resultado = await desactivar({ variables: { id: direccion.id } });

        if (!resultado.data?.desactivarDireccion) return false;
      }}
    >
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 shrink-0 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        aria-label={t("entidades.darDeBaja")}
        title={t("entidades.darDeBaja")}
      >
        <Ban aria-hidden="true" />
      </Button>
    </ConfirmDialog>
  );
}
