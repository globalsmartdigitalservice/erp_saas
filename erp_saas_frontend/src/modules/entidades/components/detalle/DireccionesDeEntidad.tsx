import { useMutation } from "@apollo/client";
import { Ban } from "lucide-react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { Dato } from "@/modules/entidades/components/detalle/DatosGenerales";
import { DialogoDireccion } from "@/modules/entidades/components/detalle/DialogoDireccion";
import { DESACTIVAR_DIRECCION } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { Direccion } from "@/modules/entidades/types/entidad.types";
import { DialogoConfirmar } from "@/shared/components/DialogoConfirmar";
import { mensajeDeError } from "@/shared/lib/errores";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
} from "@/shared/components/ui/card";


export function DireccionesDeEntidad({
  entidadId,
  direcciones,
}: {
  entidadId: string;
  direcciones: Direccion[];
}) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-end">
        <DialogoDireccion entidadId={entidadId} />
      </CardHeader>

      <CardContent>
        {direcciones.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("entidades.sinDirecciones")}
          </p>
        ) : (
          <ul className="divide-y">
            {direcciones.map((direccion) => (
              <li
                key={direccion.id}
                className="flex items-start gap-2 py-3 first:pt-0 last:pb-0"
              >
                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-2">
                    <Badge variant="secondary">
                      {direccion.tipo?.nombre ?? "—"}
                    </Badge>
                    {direccion.estado && (
                      <span className="text-xs text-muted-foreground">
                        {direccion.estado.nombre}
                      </span>
                    )}
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

  const [desactivar, { loading, error, reset }] = useMutation(DESACTIVAR_DIRECCION, {
    refetchQueries: [ENTIDAD],
  });

  return (
    <DialogoConfirmar
      titulo={t("entidades.bajaDireccionTitulo")}
      descripcion={t("entidades.bajaDireccionAyuda")}
      etiquetaConfirmar={t("entidades.darDeBaja")}
      cargando={loading}
      error={mensajeDeError(error, t)}
      alCerrar={reset}
      onConfirmar={async () => {
        const resultado = await desactivar({ variables: { id: direccion.id } });

        if (!resultado.data?.desactivarDireccion) return false;

        toast.success(t("entidades.direccionDadaDeBaja"));
      }}
    >
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 shrink-0 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        title={t("entidades.darDeBaja")}
      >
        <Ban size={15} />
        <span className="sr-only">{t("entidades.darDeBaja")}</span>
      </Button>
    </DialogoConfirmar>
  );
}
