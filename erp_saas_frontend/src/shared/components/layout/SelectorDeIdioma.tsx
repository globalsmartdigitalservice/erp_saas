import { useQuery } from "@apollo/client";
import { Check, Languages } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { IDIOMAS_ACTIVOS } from "@/shared/graphql/idiomas.queries";
import { cn } from "@/shared/lib/utils";
import { usePreferencias } from "@/shared/preferencias";
import type { Idioma } from "@/shared/types/idioma.types";

const ESPERA_AL_SALIR = 120;

export function SelectorDeIdioma() {
  const { t } = useTranslation();
  const { idiomaId, idiomaCodigo, elegirIdioma } = usePreferencias();
  const { data, loading } = useQuery<{ idiomas: Idioma[] }>(IDIOMAS_ACTIVOS);

  const [abierto, setAbierto] = useState(false);
  const temporizador = useRef<number | null>(null);

  function cancelarCierre() {
    if (temporizador.current !== null) {
      window.clearTimeout(temporizador.current);
      temporizador.current = null;
    }
  }

  function abrir() {
    cancelarCierre();
    setAbierto(true);
  }

  function cerrarConEspera() {
    cancelarCierre();
    temporizador.current = window.setTimeout(
      () => setAbierto(false),
      ESPERA_AL_SALIR,
    );
  }

  useEffect(() => cancelarCierre, []);

  const idiomas = data?.idiomas ?? [];
  const deshabilitado = loading || idiomas.length === 0;

  return (
    <DropdownMenu open={abierto} onOpenChange={setAbierto} modal={false}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          disabled={deshabilitado}
          aria-label={t("cabecera.idioma")}
          title={t("cabecera.idioma")}
          onMouseEnter={abrir}
          onMouseLeave={cerrarConEspera}
          className={cn(
            "flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-muted-foreground transition-colors",
            "hover:bg-muted hover:text-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            "disabled:pointer-events-none disabled:opacity-50",
            abierto && "bg-muted text-foreground",
          )}
        >
          <Languages size={20} />
          <span className="rounded bg-primary px-1.5 py-0.5 text-[11px] font-semibold uppercase leading-none text-primary-foreground">
            {idiomaCodigo}
          </span>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        sideOffset={6}
        onMouseEnter={abrir}
        onMouseLeave={cerrarConEspera}
        className="min-w-[11rem]"
      >
        {idiomas.map((idioma) => {
          const activo = idioma.id === idiomaId;

          return (
            <DropdownMenuItem
              key={idioma.id}
              onSelect={() => elegirIdioma(idioma.id, idioma.codigo)}
              className={cn(
                "cursor-pointer justify-between gap-3",
                activo && "font-semibold",
              )}
            >
              <span className="flex items-center gap-2.5">
                <span className="w-6 text-xs uppercase text-muted-foreground">
                  {idioma.codigo}
                </span>
                {idioma.nombre}
              </span>

              <Check
                size={15}
                className={cn("shrink-0", activo ? "opacity-100" : "opacity-0")}
              />
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
