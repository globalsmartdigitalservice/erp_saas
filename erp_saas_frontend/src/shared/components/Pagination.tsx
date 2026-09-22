import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/shared/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/shared/components/ui/tooltip";
import { cn } from "@/shared/lib/utils";

/** Hasta acá se recorre página por página; más allá, se llega filtrando. */
const MAX_NAVIGABLE_ROWS = 10_000;
const ARROW_CLASS = "h-8 w-8 text-muted-foreground [&_svg]:size-3.5";

type Props = {
  total: number;
  limit: number;
  offset: number;
  onChange: (offset: number) => void;
};

export function Pagination({ total, limit, offset, onChange }: Props) {
  const { t, i18n } = useTranslation();

  if (total === 0 || total <= limit) return null;

  const formatNumber = (value: number) => value.toLocaleString(i18n.language);

  const isCapReached = total > MAX_NAVIGABLE_ROWS;
  const navigableTotal = Math.min(total, MAX_NAVIGABLE_ROWS);
  const pageCount = Math.ceil(navigableTotal / limit);

  const currentPage = Math.floor(offset / limit) + 1;
  const first = offset + 1;
  const last = Math.min(offset + limit, navigableTotal);

  const goTo = (page: number) => onChange((page - 1) * limit);

  const pages = Array.from({ length: pageCount }, (_, i) => i + 1)
    .filter((p) => p === 1 || p === pageCount || Math.abs(p - currentPage) <= 1)
    .reduce<(number | "...")[]>((acc, p, i, arr) => {
      if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push("...");
      acc.push(p);
      return acc;
    }, []);

  return (
    <nav
      aria-label={t("paginacion.navegacion")}
      className="flex flex-col items-center justify-between gap-4 border-t bg-card px-5 py-4 sm:flex-row"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <p className="text-xs text-muted-foreground">
          {t("paginacion.mostrando", {
            inicio: formatNumber(first),
            fin: formatNumber(last),
            total: formatNumber(total),
          })}
        </p>

        {isCapReached && (
          <Tooltip>
            <TooltipTrigger asChild>
              <span
                tabIndex={0}
                className="flex cursor-help items-center gap-1.5 rounded-md border bg-muted px-2 py-1 text-muted-foreground"
              >
                <AlertTriangle aria-hidden="true" className="size-3" />
                <span className="text-[10px] font-medium uppercase tracking-wider">
                  {t("paginacion.tope")}
                </span>
              </span>
            </TooltipTrigger>
            <TooltipContent className="max-w-xs">
              {t("paginacion.topeAyuda", { max: formatNumber(MAX_NAVIGABLE_ROWS) })}
            </TooltipContent>
          </Tooltip>
        )}
      </div>

      <div className="flex items-center gap-1.5">
        <Button
          variant="outline"
          size="icon"
          onClick={() => goTo(1)}
          disabled={currentPage === 1}
          className={cn(ARROW_CLASS, "hidden sm:inline-flex")}
          aria-label={t("paginacion.primera")}
        >
          <ChevronsLeft aria-hidden="true" />
        </Button>

        <Button
          variant="outline"
          size="icon"
          onClick={() => goTo(currentPage - 1)}
          disabled={currentPage === 1}
          className={ARROW_CLASS}
          aria-label={t("paginacion.anterior")}
        >
          <ChevronLeft aria-hidden="true" />
        </Button>

        <div className="mx-1 flex items-center gap-1">
          {pages.map((p, i) =>
            p === "..." ? (
              <span
                key={`gap-${i}`}
                aria-hidden="true"
                className="px-2 text-xs font-medium text-muted-foreground"
              >
                …
              </span>
            ) : (
              <Button
                key={p}
                variant={p === currentPage ? "default" : "outline"}
                onClick={() => goTo(p)}
                aria-label={t("paginacion.pagina", { numero: p })}
                aria-current={p === currentPage ? "page" : undefined}
                className={cn(
                  "h-8 w-8 text-xs font-bold",
                  p === currentPage ? "shadow-sm shadow-primary/30" : "text-muted-foreground",
                )}
              >
                {p}
              </Button>
            ),
          )}
        </div>

        <Button
          variant="outline"
          size="icon"
          onClick={() => goTo(currentPage + 1)}
          disabled={currentPage === pageCount}
          className={ARROW_CLASS}
          aria-label={t("paginacion.siguiente")}
        >
          <ChevronRight aria-hidden="true" />
        </Button>

        <Button
          variant="outline"
          size="icon"
          onClick={() => goTo(pageCount)}
          disabled={currentPage === pageCount}
          className={cn(ARROW_CLASS, "hidden sm:inline-flex")}
          aria-label={t("paginacion.ultima")}
        >
          <ChevronsRight aria-hidden="true" />
        </Button>
      </div>
    </nav>
  );
}
