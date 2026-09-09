import React from "react";
import type { LucideIcon } from "lucide-react";
import { RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";
import { TableRow, TableCell } from "@/shared/components/ui/table";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import {
  Empty,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  EmptyDescription,
  EmptyContent,
} from "@/shared/components/ui/empty";



export function FilaEstadoTabla({
  colSpan,
  children,
}: {
  colSpan: number;
  children: React.ReactNode;
}) {
  return (
    <TableRow className="hover:bg-transparent">
      <TableCell colSpan={colSpan} className="p-0">
        {children}
      </TableCell>
    </TableRow>
  );
}


export function FilasEsqueleto({
  columnas,
  filas = 5,
}: {
  columnas: number;
  filas?: number;
}) {

  const anchos = ["w-1/2", "w-3/4", "w-2/3", "w-1/3", "w-5/6", "w-2/5"];
  return (
    <>
      {Array.from({ length: filas }).map((_, fila) => (
        <TableRow key={fila} className="hover:bg-transparent">
          {Array.from({ length: columnas }).map((_, col) => (
            <TableCell key={col} className="py-4">
              <Skeleton className={`h-4 ${anchos[col % anchos.length]}`} />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}


export function EstadoVacio({
  icono: Icono,
  titulo,
  descripcion,
  accion,
}: {
  icono: LucideIcon;
  titulo: string;
  descripcion?: string;
  accion?: React.ReactNode;
}) {
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Icono />
        </EmptyMedia>
        <EmptyTitle>{titulo}</EmptyTitle>
        {descripcion && <EmptyDescription>{descripcion}</EmptyDescription>}
      </EmptyHeader>
      {accion && <EmptyContent>{accion}</EmptyContent>}
    </Empty>
  );
}


export function EstadoError({
  icono: Icono,
  titulo,
  mensaje,
  onReintentar,
  reintentando = false,
}: {
  icono: LucideIcon;
  titulo?: string;
  mensaje?: string;
  onReintentar?: () => void;
  reintentando?: boolean;
}) {

  const { t } = useTranslation();
  titulo = titulo ?? t("comun.error");

  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon" className="bg-destructive/10 text-destructive">
          <Icono />
        </EmptyMedia>
        <EmptyTitle>{titulo}</EmptyTitle>
        {mensaje && <EmptyDescription>{mensaje}</EmptyDescription>}
      </EmptyHeader>
      {onReintentar && (
        <EmptyContent>
          <Button
            variant="outline"
            size="sm"
            onClick={onReintentar}
            disabled={reintentando}
            className="gap-2"
          >
            <RefreshCw size={14} className={reintentando ? "animate-spin" : ""} />
            {reintentando ? t("comun.cargando") : t("comun.reintentar")}
          </Button>
        </EmptyContent>
      )}
    </Empty>
  );
}
