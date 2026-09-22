import { useMutation, type ApolloError } from "@apollo/client";
import { Ban, Tags } from "lucide-react";
import { useTranslation } from "react-i18next";

import { DialogoCategoria } from "@/modules/entidades/components/categorias/DialogoCategoria";
import { DESACTIVAR_CATEGORIA } from "@/modules/entidades/graphql/entidades.mutations";
import { CATEGORIAS_ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { CategoriaEntidad } from "@/modules/entidades/types/entidad.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import {
  DataTableBody,
  DataTableHeader,
  DataTableRow,
  DataTable,
} from "@/shared/components/DataTable";
import { EmptyState } from "@/shared/components/TableStates";
import { Button } from "@/shared/components/ui/button";
import { TableCell, TableHead } from "@/shared/components/ui/table";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";
import { formatearMonto } from "@/shared/lib/formatearMonto";

const COLUMNAS = 5;

export function TablaCategorias({
  categorias,
  cargando,
  error,
  onReintentar,
}: {
  categorias: CategoriaEntidad[];
  cargando: boolean;
  error?: ApolloError;
  onReintentar?: () => void;
}) {
  const { t, i18n } = useTranslation();
  const activoId = useEstadoActivoId();

  return (
    <DataTable>
      <DataTableHeader>
        <TableHead>{t("categorias.nombre")}</TableHead>
        <TableHead>{t("categorias.descripcion")}</TableHead>
        <TableHead className="text-right">{t("categorias.descuento")}</TableHead>
        <TableHead>{t("categorias.estado")}</TableHead>
        <TableHead className="w-20" />
      </DataTableHeader>

      <DataTableBody
        columns={COLUMNAS}
        isLoading={cargando}
        error={error}
        onRetry={onReintentar}
        isEmpty={categorias.length === 0}
        empty={
          <EmptyState
            icon={Tags}
            title={t("categorias.sinCategorias")}
            description={t("categorias.sinCategoriasAyuda")}
          />
        }
      >
        {categorias.map((categoria, indice) => (
          <DataTableRow key={categoria.id} index={indice}>
            <TableCell className="font-medium">{categoria.nombre}</TableCell>
            <TableCell className="text-muted-foreground">
              {categoria.descripcion || "—"}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatearMonto(categoria.descuentoCategCliente, i18n.language)} %
            </TableCell>
            <TableCell>
              <BadgeDeEstado estado={categoria.estado} activoId={activoId} />
            </TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <DialogoCategoria categoria={categoria} />
                <BajaDeCategoria categoria={categoria} />
              </div>
            </TableCell>
          </DataTableRow>
        ))}
      </DataTableBody>
    </DataTable>
  );
}

function BajaDeCategoria({ categoria }: { categoria: CategoriaEntidad }) {
  const { t } = useTranslation();

  const [desactivar, mutacion] = useMutation(
    DESACTIVAR_CATEGORIA,
    { refetchQueries: [CATEGORIAS_ENTIDAD] },
  );

  return (
    <ConfirmDialog
      title={t("categorias.bajaTitulo", { nombre: categoria.nombre })}
      description={t("categorias.bajaAyuda")}
      confirmLabel={t("categorias.darDeBaja")}
      mutation={mutacion}
      successMessage={t("categorias.dadaDeBaja")}
      onConfirm={async () => {
        const resultado = await desactivar({
          variables: { id: categoria.id },
        });

        if (!resultado.data?.desactivarCategoriaEntidad) return false;
      }}
    >
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        aria-label={t("categorias.darDeBaja")}
        title={t("categorias.darDeBaja")}
      >
        <Ban aria-hidden="true" />
      </Button>
    </ConfirmDialog>
  );
}
