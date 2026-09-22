import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

type Props = {
  titulo: string;
  ayuda: string;
  children: ReactNode;
};

export function AccesoLayout({ titulo, ayuda, children }: Props) {
  const { t } = useTranslation();

  return (
    <main className="grid min-h-screen lg:grid-cols-[1fr_1.15fr]">
      <aside className="relative hidden overflow-hidden bg-sidebar p-12 text-sidebar-foreground lg:flex lg:flex-col lg:justify-between">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-24 -top-24 size-96 rounded-full bg-primary opacity-20 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-32 -left-16 size-80 rounded-full bg-primary opacity-10 blur-3xl"
        />

        <p className="font-heading text-2xl font-semibold tracking-tight">ERP</p>

        <div className="relative max-w-sm space-y-3">
          <p className="font-heading text-3xl font-semibold leading-tight">
            {t("login.panelTitulo")}
          </p>
          <p className="text-sm leading-relaxed text-sidebar-foreground/70">
            {t("login.panelTexto")}
          </p>
        </div>

        <div
          aria-hidden="true"
          className="h-1 w-16 rounded-full bg-primary"
        />
      </aside>

      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm space-y-8">
          <header className="space-y-2">
            <p className="font-heading text-xl font-semibold tracking-tight lg:hidden">
              ERP
            </p>
            <h1 className="font-heading text-2xl font-semibold tracking-tight">
              {titulo}
            </h1>
            <p className="text-sm text-muted-foreground">{ayuda}</p>
          </header>

          {children}
        </div>
      </div>
    </main>
  );
}
