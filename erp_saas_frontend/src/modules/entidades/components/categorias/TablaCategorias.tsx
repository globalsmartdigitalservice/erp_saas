import { useMutation } from "@apollo/client";
import { AlertTriangle, Ban, Tags } from "lucide-react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { DialogoCategoria } from "@/modules/entidades/components/categorias/DialogoCategoria";
import { DESACTIVAR_CATEGORIA } from "@/modules/entidades/graphql/entidades.mutations";
import { CATEGORIAS_ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { CategoriaEntidad } from "@/modules/entidades/types/entidad.types";
import { DialogoConfirmar } from "@/shared/components/DialogoConfirmar";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { mensajeDeError } from "@/shared/lib/errores";
import {
  EstadoError,
  EstadoVacio,
  FilaEstadoTabla,
  FilasEsqueleto,
} from "@/shared/components/EstadosTabla";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";



const COLUMNAS = 5;

export function TablaCategorias({
  categorias,
  cargando,
  error,
  onReintentar,
}: {
  categorias: CategoriaEntidad[];
  cargando: boolean;
  error?: boolean;
  onReintentar?: () => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t("categorias.nombre")}</TableHead>
            <TableHead>{t("categorias.descripcion")}</TableHead>
            <TableHead className="text-right">
              {t("categorias.descuento")}
            </TableHead>
            <TableHead>{t("categorias.estado")}</TableHead>
            <TableHead className="w-20" />
          </TableRow>
        </TableHeader>

        <TableBody>
          {cargando ? (
            <FilasEsqueleto columnas={COLUMNAS} />
          ) : error ? (
            <FilaEstadoTabla colSpan={COLUMNAS}>
              <EstadoError icono={AlertTriangle} onReintentar={onReintentar} />
            </FilaEstadoTabla>
          ) : categorias.length === 0 ? (
            <FilaEstadoTabla colSpan={COLUMNAS}>
              <EstadoVacio
                icono={Tags}
                titulo={t("categorias.sinCategorias")}
                descripcion={t("categorias.sinCategoriasAyuda")}
              />
            </FilaEstadoTabla>
          ) : (
            categorias.map((categoria) => (
              <TableRow key={categoria.id}>
                <TableCell className="font-medium">
                  {categoria.nombre}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {categoria.descripcion || "—"}
                </TableCell>
                <TableCell className="text-right tabular-nums">
     
                  {categoria.descuentoCategCliente} %
                </TableCell>
                <TableCell>
                  {categoria.estado && (
                    <Badge variant="secondary">{categoria.estado.nombre}</Badge>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <DialogoCategoria categoria={categoria} />
                    <BajaDeCategoria categoria={categoria} />
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}


function BajaDeCategoria({ categoria }: { categoria: CategoriaEntidad }) {
  const { t } = useTranslation();

  const [desactivar, { loading, error, reset }] = useMutation(
    DESACTIVAR_CATEGORIA,
    { refetchQueries: [CATEGORIAS_ENTIDAD] },
  );

  return (
    <DialogoConfirmar
      titulo={t("categorias.bajaTitulo", { nombre: categoria.nombre })}
      descripcion={t("categorias.bajaAyuda")}
      etiquetaConfirmar={t("categorias.darDeBaja")}
      cargando={loading}
      error={mensajeDeError(error, t)}
      alCerrar={reset}
      onConfirmar={async () => {
        const resultado = await desactivar({
          variables: { id: categoria.id },
        });

        if (!resultado.data?.desactivarCategoriaEntidad) return false;

        toast.success(t("categorias.dadaDeBaja"));
      }}
    >
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        title={t("categorias.darDeBaja")}
      >
        <Ban size={15} />
        <span className="sr-only">{t("categorias.darDeBaja")}</span>
      </Button>
    </DialogoConfirmar>
  );
}
