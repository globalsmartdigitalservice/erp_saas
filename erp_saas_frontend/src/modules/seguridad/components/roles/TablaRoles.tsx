import type { ApolloError } from "@apollo/client";
import { Building2, KeySquare, Pencil, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import type { Rol } from "@/modules/seguridad/types/rol.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import {
  DataTableBody,
  DataTableHeader,
  DataTableRow,
  DataTable,
} from "@/shared/components/DataTable";
import { EmptyState } from "@/shared/components/TableStates";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { TableCell, TableHead } from "@/shared/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/shared/components/ui/tooltip";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";

const COLUMNAS = 4;

type Props = {
  roles: Rol[];
  nombresDeEstado: Map<string, string>;
  cargando: boolean;
  error?: ApolloError;
  buscando: boolean;
  onReintentar: () => void;
  onEditar: (rol: Rol) => void;
};

export function TablaRoles({
  roles,
  nombresDeEstado,
  cargando,
  error,
  buscando,
  onReintentar,
  onEditar,
}: Props) {
  const { t } = useTranslation();
  const activoId = useEstadoActivoId();

  return (
    <DataTable>
      <DataTableHeader>
        <TableHead>{t("roles.nombre")}</TableHead>
        <TableHead>{t("roles.permisos")}</TableHead>
        <TableHead>{t("roles.estado")}</TableHead>
        <TableHead className="w-0 text-right">{t("roles.acciones")}</TableHead>
      </DataTableHeader>

      <DataTableBody
        columns={COLUMNAS}
        isLoading={cargando}
        error={error}
        onRetry={onReintentar}
        isEmpty={roles.length === 0}
        empty={
          <EmptyState
            icon={ShieldCheck}
            title={buscando ? t("roles.sinResultados") : t("roles.sinRoles")}
            description={
              buscando ? t("roles.sinResultadosAyuda") : t("roles.sinRolesAyuda")
            }
          />
        }
      >
        {roles.map((rol, indice) => (
          <FilaRol
            key={rol.id}
            rol={rol}
            nombreDeEstado={nombresDeEstado.get(rol.estadoId)}
            activoId={activoId}
            indice={indice}
            onEditar={onEditar}
          />
        ))}
      </DataTableBody>
    </DataTable>
  );
}

function FilaRol({
  rol,
  nombreDeEstado,
  activoId,
  indice,
  onEditar,
}: {
  rol: Rol;
  nombreDeEstado?: string;
  activoId: string | null;
  indice: number;
  onEditar: (rol: Rol) => void;
}) {
  const { t } = useTranslation();

  return (
    <DataTableRow index={indice} to={rol.id}>
      <TableCell>
        <div className="flex items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldCheck className="size-4" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <Link
              to={rol.id}
              className="block truncate rounded-sm font-medium underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {rol.nombre}
            </Link>
            {rol.esHeredado && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span
                    tabIndex={0}
                    className="inline-flex items-center gap-1 text-xs text-muted-foreground"
                  >
                    <Building2 className="size-3" aria-hidden="true" />
                    {t("roles.heredado")}
                  </span>
                </TooltipTrigger>
                <TooltipContent>{t("roles.heredadoAyuda")}</TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>
      </TableCell>

      <TableCell>
        <Badge variant="outline" className="gap-1 font-normal tabular-nums">
          <KeySquare className="size-3" aria-hidden="true" />
          {rol.cantidadPermisos ?? 0}
        </Badge>
      </TableCell>

      <TableCell>
        {nombreDeEstado && (
          <BadgeDeEstado
            estado={{ id: rol.estadoId, nombre: nombreDeEstado }}
            activoId={activoId}
          />
        )}
      </TableCell>

      <TableCell className="text-right">
        {!rol.esHeredado && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="gap-2"
            onClick={() => onEditar(rol)}
          >
            <Pencil className="size-3.5" aria-hidden="true" />
            {t("roles.editar")}
          </Button>
        )}
      </TableCell>
    </DataTableRow>
  );
}
