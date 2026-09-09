import { Menu } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Brand } from "./Brand";
import { EmpresaDeLaSesion } from "./EmpresaDeLaSesion";
import { MenuDeUsuario } from "./MenuDeUsuario";
import { SelectorDeIdioma } from "./SelectorDeIdioma";



type Props = {
  alAbrirMenu: () => void;
};

export function Header({ alAbrirMenu }: Props) {
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background px-4">
      <button
        type="button"
        onClick={alAbrirMenu}
        aria-label={t("menu.abrir")}
        className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:hidden"
      >
        <Menu size={22} />
      </button>

     
      <div className="md:hidden">
        <Brand />
      </div>

      <div className="ml-auto flex min-w-0 items-center gap-3">
        <EmpresaDeLaSesion />
        <SelectorDeIdioma />
        <MenuDeUsuario />
      </div>
    </header>
  );
}
