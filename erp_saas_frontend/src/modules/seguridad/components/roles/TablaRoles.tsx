import { AlertTriangle, Building2, KeySquare, Pencil, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import type { Rol } from "@/modules/seguridad/types/rol.types";
import {
  EstadoError,
  EstadoVacio,
  FilaEstadoTabla,
  FilasEsqueleto,
} from "@/shared/components/EstadosTabla";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/shared/components/ui/tooltip";

const COLUMNAS = 4;
const RETRASO_POR_FILA_MS = 30;
const FILAS_ESCALONADAS = 12;

type Props = {
  roles: Rol[];
  nombresDeEstado: Map<string, string>;
  cargando: boolean;
  error?: string;
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

  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/40 hover:bg-muted/40">
            <TableHead>{t("roles.nombre")}</TableHead>
            <TableHead>{t("roles.permisos")}</TableHead>
            <TableHead>{t("roles.estado")}</TableHead>
            <TableHead className="w-0 text-right">{t("roles.acciones")}</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {cargando ? (
            <FilasEsqueleto columnas={COLUMNAS} />
          ) : error ? (
            <FilaEstadoTabla colSpan={COLUMNAS}>
              <EstadoError icono={AlertTriangle} mensaje={error} onReintentar={onReintentar} />
            </FilaEstadoTabla>
          ) : roles.length === 0 ? (
            <FilaEstadoTabla colSpan={COLUMNAS}>
              <EstadoVacio
                icono={ShieldCheck}
                titulo={buscando ? t("roles.sinResultados") : t("roles.sinRoles")}
                descripcion={
                  buscando ? t("roles.sinResultadosAyuda") : t("roles.sinRolesAyuda")
                }
              />
            </FilaEstadoTabla>
          ) : (
            roles.map((rol, indice) => (
              <FilaRol
                key={rol.id}
                rol={rol}
                estado={nombresDeEstado.get(rol.estadoId)}
                indice={indice}
                onEditar={onEditar}
              />
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function FilaRol({
  rol,
  estado,
  indice,
  onEditar,
}: {
  rol: Rol;
  estado?: string;
  indice: number;
  onEditar: (rol: Rol) => void;
}) {
  const { t } = useTranslation();

  return (
    <TableRow
      className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-1 fill-mode-both"
      style={{
        animationDelay: `${Math.min(indice, FILAS_ESCALONADAS) * RETRASO_POR_FILA_MS}ms`,
      }}
    >
      <TableCell>
        <div className="flex items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldCheck className="size-4" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <Link
              to={rol.id}
              className="block truncate font-medium underline-offset-4 hover:underline focus-visible:underline focus-visible:outline-none"
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

      <TableCell>{estado && <Badge variant="secondary">{estado}</Badge>}</TableCell>

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
    </TableRow>
  );
}
