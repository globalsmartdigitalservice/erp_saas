import type { ApolloError } from "@apollo/client";
import { Users } from "lucide-react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  nombreCompleto,
  type Entidad,
} from "@/modules/entidades/types/entidad.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import {
  DataTableBody,
  DataTableHeader,
  DataTableRow,
  DataTable,
} from "@/shared/components/DataTable";
import { EmptyState } from "@/shared/components/TableStates";
import { TableCell, TableHead } from "@/shared/components/ui/table";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";

const COLUMNAS = 5;

type Props = {
  entidades: Entidad[];
  cargando: boolean;
  error?: ApolloError;
  onReintentar?: () => void;
};

export function TablaEntidades({
  entidades,
  cargando,
  error,
  onReintentar,
}: Props) {
  const { t } = useTranslation();
  const activoId = useEstadoActivoId();

  return (
    <DataTable>
      <DataTableHeader>
        <TableHead>{t("entidades.nombre")}</TableHead>
        <TableHead>{t("entidades.tipo")}</TableHead>
        <TableHead>{t("entidades.documento")}</TableHead>
        <TableHead>{t("entidades.tipoDocumento")}</TableHead>
        <TableHead>{t("entidades.estado")}</TableHead>
      </DataTableHeader>

      <DataTableBody
        columns={COLUMNAS}
        isLoading={cargando}
        error={error}
        onRetry={onReintentar}
        isEmpty={entidades.length === 0}
        empty={
          <EmptyState
            icon={Users}
            title={t("entidades.sinEntidades")}
            description={t("entidades.sinEntidadesAyuda")}
          />
        }
      >
        {entidades.map((entidad, indice) => (
          <DataTableRow key={entidad.id} index={indice} to={entidad.id}>
            <TableCell className="font-medium">
              <Link
                to={entidad.id}
                className="rounded-sm hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {nombreCompleto(entidad)}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {entidad.tipoEntidad?.nombre ?? "—"}
            </TableCell>
            <TableCell>
              {entidad.documento || (
                <span className="text-muted-foreground">
                  {t("entidades.sinDocumento")}
                </span>
              )}
            </TableCell>
            <TableCell className="text-muted-foreground">
              {entidad.tipoDocumento?.nombre ?? "—"}
            </TableCell>
            <TableCell>
              <BadgeDeEstado estado={entidad.estado} activoId={activoId} />
            </TableCell>
          </DataTableRow>
        ))}
      </DataTableBody>
    </DataTable>
  );
}
