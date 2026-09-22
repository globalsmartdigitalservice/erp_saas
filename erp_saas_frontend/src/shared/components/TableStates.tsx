import type { ApolloError } from "@apollo/client";
import { AlertTriangle, RefreshCw, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/shared/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/shared/components/ui/empty";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { TableCell, TableRow } from "@/shared/components/ui/table";
import { mensajeDeError } from "@/shared/lib/errores";

const SKELETON_WIDTHS = ["w-1/2", "w-3/4", "w-2/3", "w-1/3", "w-5/6", "w-2/5"];

export function TableStateRow({
  colSpan,
  children,
}: {
  colSpan: number;
  children: ReactNode;
}) {
  return (
    <TableRow className="hover:bg-transparent">
      <TableCell colSpan={colSpan} className="p-0">
        {children}
      </TableCell>
    </TableRow>
  );
}

export function SkeletonRows({
  columns,
  rows = 5,
}: {
  columns: number;
  rows?: number;
}) {
  return (
    <>
      {Array.from({ length: rows }).map((_, row) => (
        <TableRow key={row} className="hover:bg-transparent">
          {Array.from({ length: columns }).map((_, column) => (
            <TableCell key={column} className="py-4">
              <Skeleton
                className={`h-4 ${SKELETON_WIDTHS[column % SKELETON_WIDTHS.length]}`}
              />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Icon aria-hidden="true" />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        {description && <EmptyDescription>{description}</EmptyDescription>}
      </EmptyHeader>
      {action && <EmptyContent>{action}</EmptyContent>}
    </Empty>
  );
}

/** El error de una consulta; el texto lo arma `mensajeDeError`. */
export function ErrorState({
  error,
  icon: Icon = AlertTriangle,
  title,
  onRetry,
  isRetrying = false,
}: {
  error: ApolloError | undefined;
  icon?: LucideIcon;
  title?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
}) {
  const { t } = useTranslation();
  const message = mensajeDeError(error, t);

  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon" className="bg-destructive/10 text-destructive">
          <Icon aria-hidden="true" />
        </EmptyMedia>
        <EmptyTitle>{title ?? t("comun.error")}</EmptyTitle>
        {message && <EmptyDescription>{message}</EmptyDescription>}
      </EmptyHeader>
      {onRetry && (
        <EmptyContent>
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            disabled={isRetrying}
            aria-busy={isRetrying || undefined}
            className="gap-2"
          >
            <RefreshCw
              aria-hidden="true"
              className={isRetrying ? "animate-spin" : undefined}
            />
            {isRetrying ? t("comun.cargando") : t("comun.reintentar")}
          </Button>
        </EmptyContent>
      )}
    </Empty>
  );
}
