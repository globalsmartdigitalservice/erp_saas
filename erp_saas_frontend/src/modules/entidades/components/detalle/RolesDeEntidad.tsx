import { useMutation } from "@apollo/client";
import { Ban, Tags } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Dato } from "@/modules/entidades/components/detalle/DatosGenerales";
import { DialogoRol } from "@/modules/entidades/components/detalle/DialogoRol";
import { DESACTIVAR_ROL } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { RolEntidad } from "@/modules/entidades/types/entidad.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { EmptyState } from "@/shared/components/TableStates";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/shared/components/ui/card";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";
import { formatearMonto } from "@/shared/lib/formatearMonto";

export function RolesDeEntidad({
  entidadId,
  roles,
}: {
  entidadId: string;
  roles: RolEntidad[];
}) {
  const { t, i18n } = useTranslation();
  const activoId = useEstadoActivoId();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-4 space-y-0">
        <CardDescription>{t("entidades.rolesAyuda")}</CardDescription>
        <DialogoRol entidadId={entidadId} />
      </CardHeader>

      <CardContent>
        {roles.length === 0 ? (
          <EmptyState icon={Tags} title={t("entidades.sinRoles")} />
        ) : (
          <ul className="divide-y">
            {roles.map((rol) => (
              <li
                key={rol.id}
                className="flex items-start gap-2 py-3 first:pt-0 last:pb-0"
              >
                <div className="grid min-w-0 flex-1 gap-4 sm:grid-cols-4">
                  <div className="flex items-start">
                    <Badge>{rol.tipoRol?.nombre ?? "—"}</Badge>
                  </div>
                  <Dato etiqueta={t("entidades.categoria")}>
                    {rol.categoria?.nombre}
                  </Dato>
                  <Dato etiqueta={t("entidades.limiteCredito")}>
                    <span className="tabular-nums">
                      {formatearMonto(rol.limiteCredito, i18n.language)}
                    </span>
                  </Dato>
                  <Dato etiqueta={t("entidades.estado")}>
                    <BadgeDeEstado estado={rol.estado} activoId={activoId} />
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

  const [desactivar, mutacion] = useMutation(DESACTIVAR_ROL, {
    refetchQueries: [ENTIDAD],
  });

  return (
    <ConfirmDialog
      title={t("entidades.bajaRolTitulo", {
        rol: rol.tipoRol?.nombre ?? "",
      })}
      description={t("entidades.bajaRolAyuda")}
      confirmLabel={t("entidades.darDeBaja")}
      mutation={mutacion}
      successMessage={t("entidades.rolDadoDeBaja")}
      onConfirm={async () => {
        const resultado = await desactivar({ variables: { id: rol.id } });

        if (!resultado.data?.desactivarRolEntidad) return false;
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
