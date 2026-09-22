import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/shared/components/ui/breadcrumb";

import { findMenuLocation } from "./menu";

/** Módulo › pantalla; la pantalla es un enlace solo desde una ficha o un alta. */
export function Breadcrumbs() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const location = findMenuLocation(pathname);

  if (location === null) return null;

  const { modulo, pantalla } = location;

  return (
    <Breadcrumb className="hidden min-w-0 md:block">
      <BreadcrumbList>
        <BreadcrumbItem>{t(modulo.clave)}</BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          {pathname === pantalla.ruta ? (
            <BreadcrumbPage>{t(pantalla.clave)}</BreadcrumbPage>
          ) : (
            <BreadcrumbLink asChild>
              <Link to={pantalla.ruta}>{t(pantalla.clave)}</Link>
            </BreadcrumbLink>
          )}
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
}
