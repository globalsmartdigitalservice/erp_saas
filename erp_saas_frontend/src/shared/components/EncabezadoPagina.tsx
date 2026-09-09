import React from "react";
import type { LucideIcon } from "lucide-react";

interface EncabezadoPaginaProps {
  icono?: LucideIcon;
  titulo: string;
  subtitulo?: string;
  accion?: React.ReactNode;
}

export function EncabezadoPagina({
  icono: Icono,
  titulo,
  subtitulo,
  accion,
}: EncabezadoPaginaProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex items-start gap-3">
        {Icono && (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Icono size={20} />
          </div>
        )}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            {titulo}
          </h1>
          {subtitulo && (
            <p className="mt-1 text-sm text-muted-foreground">{subtitulo}</p>
          )}
        </div>
      </div>
      {accion && <div className="shrink-0">{accion}</div>}
    </div>
  );
}
