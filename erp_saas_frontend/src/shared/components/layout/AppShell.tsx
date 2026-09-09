import { Building2 } from "lucide-react";
import { Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { EstadoVacio } from "@/shared/components/EstadosTabla";
import { TooltipProvider } from "@/shared/components/ui/tooltip";
import { useSidebar } from "@/shared/hooks/useSidebar";
import { usePreferencias } from "@/shared/preferencias";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { SidebarMobile } from "./SidebarMobile";


export function AppShell() {
  const { t } = useTranslation();
  const { empresaId } = usePreferencias();
  const {
    colapsado,
    alternarColapsado,
    abiertoEnMovil,
    abrirEnMovil,
    cerrarEnMovil,
    setAbiertoEnMovil,
  } = useSidebar();

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex min-h-screen bg-background text-foreground">
        <Sidebar colapsado={colapsado} alternarColapsado={alternarColapsado} />

        <SidebarMobile
          abierto={abiertoEnMovil}
          alCambiar={setAbiertoEnMovil}
          alCerrar={cerrarEnMovil}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <Header alAbrirMenu={abrirEnMovil} />

          <main className="flex-1 p-6">
            {empresaId === null ? (

              <EstadoVacio
                icono={Building2}
                titulo={t("cabecera.sinEmpresaTitulo")}
                descripcion={t("cabecera.sinEmpresaAyuda")}
              />
            ) : (
              <Outlet />
            )}
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}
