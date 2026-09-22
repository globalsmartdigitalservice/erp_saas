import { useRef } from "react";
import { useTranslation } from "react-i18next";
import { Outlet } from "react-router-dom";

import { TooltipProvider } from "@/shared/components/ui/tooltip";
import { useDocumentTitle } from "@/shared/hooks/useDocumentTitle";
import { useSidebar } from "@/shared/hooks/useSidebar";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { SidebarMobile } from "./SidebarMobile";

export function AppShell() {
  const { t } = useTranslation();
  const contenido = useRef<HTMLElement>(null);
  const {
    colapsado,
    alternarColapsado,
    abiertoEnMovil,
    abrirEnMovil,
    cerrarEnMovil,
    setAbiertoEnMovil,
  } = useSidebar();

  useDocumentTitle();

  return (
    <TooltipProvider delayDuration={0}>
      <a
        href="#contenido"
        onClick={(e) => {
          e.preventDefault();
          contenido.current?.focus();
        }}
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {t("menu.saltarAlContenido")}
      </a>

      <div className="flex min-h-screen bg-background text-foreground">
        <Sidebar colapsado={colapsado} alternarColapsado={alternarColapsado} />

        <SidebarMobile
          abierto={abiertoEnMovil}
          alCambiar={setAbiertoEnMovil}
          alCerrar={cerrarEnMovil}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <Header alAbrirMenu={abrirEnMovil} />

          <main
            id="contenido"
            ref={contenido}
            tabIndex={-1}
            className="flex-1 p-4 outline-none md:p-6"
          >
            <Outlet />
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}
