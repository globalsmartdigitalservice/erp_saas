import { Building2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useSession } from "@/shared/session";

/**
 * La empresa en la que está parada la sesión. SOLO LECTURA.
 *
 * Reemplaza al selector que había antes. No es un combo porque la empresa
 * sale del token firmado: cambiarla exige un token nuevo, no un clic. Ver
 * `MODULO_12_frontend.md` §4.1 — mientras eso no exista, cambiar de sucursal
 * es cerrar sesión y volver a entrar.
 */
export function EmpresaDeSesion() {
  const { t } = useTranslation();
  const { empresa } = useSession();

  if (empresa === null) return null;

  return (
    <div
      className="hidden min-w-0 items-center gap-2 text-sm sm:flex"
      aria-label={t("cabecera.empresa")}
    >
      <Building2 className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
      <span className="truncate font-medium">{empresa.razonSocial}</span>
      {!empresa.esMatriz && (
        <span className="shrink-0 text-xs text-muted-foreground">
          {t("login.sucursal")}
        </span>
      )}
    </div>
  );
}
