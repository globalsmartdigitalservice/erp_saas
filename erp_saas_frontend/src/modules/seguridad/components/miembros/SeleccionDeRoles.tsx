import { useQuery } from "@apollo/client";
import { ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

import { ROLES_ASIGNABLES } from "@/modules/seguridad/graphql/miembros.queries";
import type { RolAsignable } from "@/modules/seguridad/types/miembro.types";
import { Checkbox } from "@/shared/components/ui/checkbox";
import { Label } from "@/shared/components/ui/label";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useEstadoId } from "@/shared/hooks/useEstadoId";
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";

type Props = {
  seleccionados: string[];
  onCambiar: (rolIds: string[]) => void;
};

export function SeleccionDeRoles({ seleccionados, onCambiar }: Props) {
  const { t } = useTranslation();
  const { id: activoId, cargando: cargandoEstados } = useEstadoId(ABREV_ACTIVO);

  const { data, loading } = useQuery<{ roles: RolAsignable[] }>(ROLES_ASIGNABLES, {
    variables: { estadoId: activoId },
    skip: activoId === null,
  });

  const roles = data?.roles ?? [];

  function alternar(rolId: string, marcado: boolean) {
    onCambiar(
      marcado ? [...seleccionados, rolId] : seleccionados.filter((id) => id !== rolId),
    );
  }

  return (
    <fieldset className="space-y-2">
      <legend className="text-sm font-medium">{t("miembros.roles")}</legend>
      <p className="text-xs text-muted-foreground">{t("miembros.rolesAyuda")}</p>

      {loading || cargandoEstados ? (
        <Skeleton className="h-16 w-full" />
      ) : roles.length === 0 ? (
        <p className="rounded-md border border-dashed px-3 py-2 text-sm text-muted-foreground">
          {t("miembros.sinRolesDisponibles")}
        </p>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2">
          {roles.map((rol) => {
            const id = `rol-${rol.id}`;
            return (
              <Label
                key={rol.id}
                htmlFor={id}
                className="flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2.5 font-normal leading-normal transition-colors hover:bg-muted/50 has-[button[data-state=checked]]:border-primary has-[button[data-state=checked]]:bg-primary/5"
              >
                <Checkbox
                  id={id}
                  checked={seleccionados.includes(rol.id)}
                  onCheckedChange={(valor) => alternar(rol.id, valor === true)}
                />
                <ShieldCheck className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                <span className="flex-1">{rol.nombre}</span>
                {rol.esHeredado && (
                  <span className="text-xs text-muted-foreground">
                    {t("miembros.rolHeredado")}
                  </span>
                )}
              </Label>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}
