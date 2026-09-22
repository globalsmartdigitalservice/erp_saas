import { Menu } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/shared/components/ui/button";

import { Brand } from "./Brand";
import { EmpresaDeSesion } from "./EmpresaDeSesion";
import { MenuDeUsuario } from "./MenuDeUsuario";
import { Breadcrumbs } from "./Breadcrumbs";
import { SelectorDeIdioma } from "./SelectorDeIdioma";

type Props = {
  alAbrirMenu: () => void;
};

export function Header({ alAbrirMenu }: Props) {
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background px-4">
      <Button
        variant="ghost"
        size="icon"
        onClick={alAbrirMenu}
        aria-label={t("menu.abrir")}
        className="size-9 text-muted-foreground md:hidden [&_svg]:size-5"
      >
        <Menu />
      </Button>

      <div className="md:hidden">
        <Brand />
      </div>

      <Breadcrumbs />

      <div className="ml-auto flex min-w-0 items-center gap-3">
        <EmpresaDeSesion />
        <SelectorDeIdioma />
        <MenuDeUsuario />
      </div>
    </header>
  );
}
