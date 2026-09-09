import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/shared/components/ui/button";


const VENTANA_MAXIMA = 10_000;

type Props = {
 
  total: number;

  limite: number;

  desde: number;

  onCambiar: (desde: number) => void;
};

export function Paginacion({ total, limite, desde, onCambiar }: Props) {
  const { t } = useTranslation();

  if (total === 0 || total <= limite) return null;

  const topeAlcanzado = total > VENTANA_MAXIMA;
  const totalNavegable = Math.min(total, VENTANA_MAXIMA);
  const totalPaginas = Math.ceil(totalNavegable / limite);

  const paginaActual = Math.floor(desde / limite) + 1;
  const inicio = desde + 1;
  const fin = Math.min(desde + limite, totalNavegable);

  const irA = (pagina: number) => onCambiar((pagina - 1) * limite);


  const paginas = Array.from({ length: totalPaginas }, (_, i) => i + 1)
    .filter(
      (p) => p === 1 || p === totalPaginas || Math.abs(p - paginaActual) <= 1,
    )
    .reduce<(number | "...")[]>((acc, p, i, arr) => {
      if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push("...");
      acc.push(p);
      return acc;
    }, []);

  return (
    <div className="flex flex-col items-center justify-between gap-4 border-t bg-card px-5 py-4 sm:flex-row">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <p className="text-xs text-muted-foreground">
          {t("paginacion.mostrando", {
            inicio,
            fin,
            total: total.toLocaleString(),
          })}
        </p>

        {topeAlcanzado && (
          <div
            className="flex cursor-help items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-amber-700"
            title={t("paginacion.topeAyuda", {
              max: VENTANA_MAXIMA.toLocaleString(),
            })}
          >
            <AlertTriangle size={12} className="text-amber-600" />
            <span className="text-[10px] font-medium uppercase tracking-wider">
              {t("paginacion.tope")}
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-1.5">
        <Button
          variant="outline"
          size="icon"
          onClick={() => irA(1)}
          disabled={paginaActual === 1}
          className="hidden h-8 w-8 text-muted-foreground sm:inline-flex"
          title={t("paginacion.primera")}
        >
          <ChevronsLeft size={14} />
        </Button>

        <Button
          variant="outline"
          size="icon"
          onClick={() => irA(paginaActual - 1)}
          disabled={paginaActual === 1}
          className="h-8 w-8 text-muted-foreground"
          title={t("paginacion.anterior")}
        >
          <ChevronLeft size={14} />
        </Button>

        <div className="mx-1 flex items-center gap-1">
          {paginas.map((p, i) =>
            p === "..." ? (
              <span
                key={`puntos-${i}`}
                className="px-2 text-xs font-medium text-muted-foreground"
              >
                …
              </span>
            ) : (
              <Button
                key={p}
                variant={p === paginaActual ? "default" : "outline"}
                onClick={() => irA(p)}
                className={`h-8 w-8 text-xs font-bold ${
                  p === paginaActual
                    ? "shadow-sm shadow-primary/30"
                    : "text-muted-foreground"
                }`}
              >
                {p}
              </Button>
            ),
          )}
        </div>

        <Button
          variant="outline"
          size="icon"
          onClick={() => irA(paginaActual + 1)}
          disabled={paginaActual === totalPaginas}
          className="h-8 w-8 text-muted-foreground"
          title={t("paginacion.siguiente")}
        >
          <ChevronRight size={14} />
        </Button>

        <Button
          variant="outline"
          size="icon"
          onClick={() => irA(totalPaginas)}
          disabled={paginaActual === totalPaginas}
          className="hidden h-8 w-8 text-muted-foreground sm:inline-flex"
          title={t("paginacion.ultima")}
        >
          <ChevronsRight size={14} />
        </Button>
      </div>
    </div>
  );
}
