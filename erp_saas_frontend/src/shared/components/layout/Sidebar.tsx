import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/shared/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/shared/components/ui/tooltip";
import { cn } from "@/shared/lib/utils";

import { Brand } from "./Brand";
import { SIDEBAR_FOCUS_RING } from "./styles";
import { SidebarNav } from "./SidebarNav";

type Props = {
  colapsado: boolean;
  alternarColapsado: () => void;
};

export function Sidebar({ colapsado, alternarColapsado }: Props) {
  const { t } = useTranslation();
  const etiqueta = colapsado ? t("menu.expandir") : t("menu.colapsar");

  return (
    <aside
      className={cn(
        "sticky top-0 z-40 hidden h-screen shrink-0 flex-col bg-sidebar text-sidebar-foreground shadow-xl transition-[width] duration-300 ease-in-out md:flex",
        colapsado ? "w-[4.75rem]" : "w-64",
      )}
    >
      <div
        className={cn(
          "flex h-16 items-center border-b border-sidebar-foreground/10",
          colapsado ? "justify-center px-2" : "justify-between px-4",
        )}
      >
        {!colapsado && <Brand />}

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={alternarColapsado}
              aria-label={etiqueta}
              className={cn(
                "size-9 rounded-lg text-sidebar-foreground/70 hover:bg-sidebar-foreground/10 hover:text-sidebar-foreground [&_svg]:size-5",
                SIDEBAR_FOCUS_RING,
              )}
            >
              {colapsado ? <PanelLeftOpen /> : <PanelLeftClose />}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">{etiqueta}</TooltipContent>
        </Tooltip>
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <SidebarNav colapsado={colapsado} />
      </div>
    </aside>
  );
}
