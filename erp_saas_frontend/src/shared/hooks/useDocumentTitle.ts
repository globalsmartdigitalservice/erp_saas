import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";

import { APP_NAME } from "@/shared/components/layout/Brand";
import { findMenuLocation } from "@/shared/components/layout/menu";

/** "Usuarios · ERP": que cada pestaña del navegador diga en qué pantalla está. */
export function useDocumentTitle() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const titleKey = findMenuLocation(pathname)?.pantalla.clave;

  useEffect(() => {
    document.title = titleKey ? `${t(titleKey)} · ${APP_NAME}` : APP_NAME;
  }, [titleKey, t]);

  // Al salir del AppShell (cerrar sesión) el login no tiene que heredar el título.
  useEffect(() => () => {
    document.title = APP_NAME;
  }, []);
}
