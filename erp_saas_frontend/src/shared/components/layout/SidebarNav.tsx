import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/shared/components/ui/accordion";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { cn } from "@/shared/lib/utils";

import { MENU, type ModuloDeMenu } from "./menu";



type Props = {
  colapsado: boolean;

  alNavegar?: () => void;
};


const RUTAS = MENU.flatMap((modulo) => modulo.pantallas.map((p) => p.ruta));


function pantallaActiva(pathname: string): string | null {
  const candidatas = RUTAS.filter(
    (ruta) => pathname === ruta || pathname.startsWith(ruta + "/"),
  );

  return candidatas.sort((a, b) => b.length - a.length)[0] ?? null;
}

function moduloDe(ruta: string | null): string | null {
  if (ruta === null) return null;

  return MENU.find((m) => m.pantallas.some((p) => p.ruta === ruta))?.id ?? null;
}

export function SidebarNav({ colapsado, alNavegar }: Props) {
  const { pathname } = useLocation();

  const activa = pantallaActiva(pathname);
  const moduloActivo = moduloDe(activa);

 
  const [abiertos, setAbiertos] = useState<string[]>(
    moduloActivo ? [moduloActivo] : [],
  );


  useEffect(() => {
    if (moduloActivo === null) return;

    setAbiertos((previos) =>
      previos.includes(moduloActivo) ? previos : [...previos, moduloActivo],
    );
  }, [moduloActivo]);

  if (colapsado) {
    return (
      <nav className="flex flex-col gap-1 px-3">
        {MENU.map((modulo) => (
          <ModuloColapsado
            key={modulo.id}
            modulo={modulo}
            activa={activa}
            esElActivo={modulo.id === moduloActivo}
            alNavegar={alNavegar}
          />
        ))}
      </nav>
    );
  }

  return (
    <nav className="px-3">
      <Accordion
        type="multiple"
        value={abiertos}
        onValueChange={setAbiertos}
        className="flex flex-col gap-1"
      >
        {MENU.map((modulo) => (
          <ModuloAbierto
            key={modulo.id}
            modulo={modulo}
            activa={activa}
            esElActivo={modulo.id === moduloActivo}
            alNavegar={alNavegar}
          />
        ))}
      </Accordion>
    </nav>
  );
}

type PropsDeModulo = {
  modulo: ModuloDeMenu;
  activa: string | null;
  esElActivo: boolean;
  alNavegar?: () => void;
};


function ModuloAbierto({
  modulo,
  activa,
  esElActivo,
  alNavegar,
}: PropsDeModulo) {
  const { t } = useTranslation();
  const Icono = modulo.icono;

  return (
    <AccordionItem value={modulo.id} className="border-b-0">
      <AccordionTrigger
        className={cn(
          "gap-3 rounded-xl px-3 py-2.5 text-sm font-medium no-underline hover:no-underline",
          "text-sidebar-foreground/70 hover:bg-sidebar-foreground/10 hover:text-sidebar-foreground",
  
          esElActivo && "text-sidebar-foreground",
        )}
      >
        <span className="flex items-center gap-3">
          <Icono size={18} className="shrink-0" />
          <span className="truncate">{t(modulo.clave)}</span>
        </span>
      </AccordionTrigger>


      <AccordionContent className="pb-0 pt-1">
        <div className="flex flex-col gap-1">
          {modulo.pantallas.map((pantalla) => (
            <NavLink
              key={pantalla.ruta}
              to={pantalla.ruta}
              onClick={alNavegar}
              className={cn(
                "relative ml-4 flex items-center rounded-xl py-2 pl-6 pr-3 text-sm transition-colors",

                "before:absolute before:left-0 before:top-0 before:h-full before:w-px before:bg-sidebar-foreground/15",
                pantalla.ruta === activa
                  ? "bg-sidebar-active font-semibold text-sidebar-active-foreground shadow-sm"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-foreground/10 hover:text-sidebar-foreground",
              )}
            >
              <span className="truncate">{t(pantalla.clave)}</span>
            </NavLink>
          ))}
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}

function ModuloColapsado({
  modulo,
  activa,
  esElActivo,
  alNavegar,
}: PropsDeModulo) {
  const { t } = useTranslation();
  const Icono = modulo.icono;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label={t(modulo.clave)}
        className={cn(
          "flex h-11 w-11 items-center justify-center rounded-xl transition-colors",
          esElActivo
            ? "bg-sidebar-active text-sidebar-active-foreground shadow-sm"
            : "text-sidebar-foreground/70 hover:bg-sidebar-foreground/10 hover:text-sidebar-foreground",
        )}
      >
        <Icono size={18} className="shrink-0" />
      </DropdownMenuTrigger>

      <DropdownMenuContent side="right" align="start" className="min-w-44">
        <DropdownMenuLabel>{t(modulo.clave)}</DropdownMenuLabel>
        <DropdownMenuSeparator />

        {modulo.pantallas.map((pantalla) => (
          <DropdownMenuItem key={pantalla.ruta} asChild>
            <NavLink
              to={pantalla.ruta}
              onClick={alNavegar}
              className={cn(
                "cursor-pointer",
                pantalla.ruta === activa && "font-semibold",
              )}
            >
              {t(pantalla.clave)}
            </NavLink>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
