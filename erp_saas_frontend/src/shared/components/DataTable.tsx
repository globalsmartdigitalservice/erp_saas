import type { ApolloError } from "@apollo/client";
import type { CSSProperties, MouseEvent, ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import {
  ErrorState,
  TableStateRow,
  SkeletonRows,
} from "@/shared/components/TableStates";
import {
  Table,
  TableBody,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { cn } from "@/shared/lib/utils";

const STAGGER_DELAY_MS = 30;
const MAX_STAGGERED_ROWS = 12;
const INTERACTIVE_SELECTOR = "a, button, input, [role='button'], [tabindex]";

export function DataTable({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      <Table>{children}</Table>
    </div>
  );
}

export function DataTableHeader({ children }: { children: ReactNode }) {
  return (
    <TableHeader className="[&_th]:h-10 [&_th]:text-xs [&_th]:font-semibold [&_th]:uppercase [&_th]:tracking-wide [&_th]:text-sidebar">
      <TableRow className="border-sidebar/10 bg-sidebar/5 hover:bg-sidebar/5">
        {children}
      </TableRow>
    </TableHeader>
  );
}

type DataTableBodyProps = {
  columns: number;
  isLoading: boolean;
  error: ApolloError | undefined;
  onRetry?: () => void;
  isEmpty: boolean;
  /** Lo que se muestra sin filas: casi siempre un `EmptyState`. */
  empty: ReactNode;
  children: ReactNode;
};

export function DataTableBody({
  columns,
  isLoading,
  error,
  onRetry,
  isEmpty,
  empty,
  children,
}: DataTableBodyProps) {
  return (
    <TableBody>
      {isLoading ? (
        <SkeletonRows columns={columns} />
      ) : error ? (
        <TableStateRow colSpan={columns}>
          <ErrorState error={error} onRetry={onRetry} />
        </TableStateRow>
      ) : isEmpty ? (
        <TableStateRow colSpan={columns}>{empty}</TableStateRow>
      ) : (
        children
      )}
    </TableBody>
  );
}

function staggerStyle(index: number): CSSProperties {
  return {
    animationDelay: `${Math.min(index, MAX_STAGGERED_ROWS) * STAGGER_DELAY_MS}ms`,
  };
}

type DataTableRowProps = {
  index: number;
  /** Con `to`, toda la fila abre esa ruta con el mouse. */
  to?: string;
  children: ReactNode;
};

/** Un clic sobre un enlace, un botón o un texto seleccionado no navega. */
export function DataTableRow({ index, to, children }: DataTableRowProps) {
  const navigate = useNavigate();

  function handleClick(event: MouseEvent<HTMLTableRowElement>) {
    if (to === undefined) return;
    // `closest` sube hasta el documento, y el <main> del marco lleva tabindex.
    const interactive = (event.target as HTMLElement).closest(INTERACTIVE_SELECTOR);
    if (interactive && event.currentTarget.contains(interactive)) return;
    if (window.getSelection()?.toString()) return;
    navigate(to);
  }

  return (
    <TableRow
      className={cn(
        "hover:bg-primary/5 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-1 fill-mode-both [&>td]:py-3",
        to !== undefined && "cursor-pointer",
      )}
      style={staggerStyle(index)}
      onClick={handleClick}
    >
      {children}
    </TableRow>
  );
}
