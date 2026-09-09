import { useMutation } from "@apollo/client";
import { Ban } from "lucide-react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { Dato } from "@/modules/entidades/components/detalle/DatosGenerales";
import { DialogoRol } from "@/modules/entidades/components/detalle/DialogoRol";
import { DESACTIVAR_ROL } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { RolEntidad } from "@/modules/entidades/types/entidad.types";
import { DialogoConfirmar } from "@/shared/components/DialogoConfirmar";
import { mensajeDeError } from "@/shared/lib/errores";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/shared/components/ui/card";


export function RolesDeEntidad({
  entidadId,
  roles,
}: {
  entidadId: string;
  roles: RolEntidad[];
}) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-4">
        <CardDescription>{t("entidades.rolesAyuda")}</CardDescription>
        <DialogoRol entidadId={entidadId} />
      </CardHeader>

      <CardContent>
        {roles.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("entidades.sinRoles")}
          </p>
        ) : (
          <ul className="divide-y">
            {roles.map((rol) => (
              <li
                key={rol.id}
                className="flex items-start gap-2 py-3 first:pt-0 last:pb-0"
              >
                <div className="grid flex-1 gap-4 sm:grid-cols-4">
                  <div className="flex items-start">
                    <Badge>{rol.tipoRol?.nombre ?? "—"}</Badge>
                  </div>
                  <Dato etiqueta={t("entidades.categoria")}>
                    {rol.categoria?.nombre}
                  </Dato>
                  <Dato etiqueta={t("entidades.limiteCredito")}>
   
                    {rol.limiteCredito}
                  </Dato>
                  <Dato etiqueta={t("entidades.estado")}>
                    {rol.estado?.nombre}
                  </Dato>
                </div>

                <div className="flex shrink-0 items-start">
                  <DialogoRol entidadId={entidadId} rol={rol} />
                  <BajaDeRol rol={rol} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}


function BajaDeRol({ rol }: { rol: RolEntidad }) {
  const { t } = useTranslation();

  const [desactivar, { loading, error, reset }] = useMutation(DESACTIVAR_ROL, {
    refetchQueries: [ENTIDAD],
  });

  return (
    <DialogoConfirmar
      titulo={t("entidades.bajaRolTitulo", {
        rol: rol.tipoRol?.nombre ?? "",
      })}
      descripcion={t("entidades.bajaRolAyuda")}
      etiquetaConfirmar={t("entidades.darDeBaja")}
      cargando={loading}
      error={mensajeDeError(error, t)}
      alCerrar={reset}
      onConfirmar={async () => {
        const resultado = await desactivar({ variables: { id: rol.id } });

  
        if (!resultado.data?.desactivarRolEntidad) return false;

        toast.success(t("entidades.rolDadoDeBaja"));
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
