import { useTranslation } from "react-i18next";

import { Sheet, SheetContent, SheetTitle } from "@/shared/components/ui/sheet";

import { Brand } from "./Brand";
import { SidebarNav } from "./SidebarNav";

type Props = {
  abierto: boolean;
  alCambiar: (abierto: boolean) => void;
  alCerrar: () => void;
};

export function SidebarMobile({ abierto, alCambiar, alCerrar }: Props) {
  const { t } = useTranslation();

  return (
    <Sheet open={abierto} onOpenChange={alCambiar}>
      <SheetContent
        side="left"
        className="flex w-72 flex-col border-none bg-sidebar p-0 text-sidebar-foreground"
      >
        <SheetTitle className="sr-only">{t("menu.navegacion")}</SheetTitle>

        <div className="flex h-16 items-center border-b border-sidebar-foreground/10 px-4">
          <Brand />
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <SidebarNav colapsado={false} alNavegar={alCerrar} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
