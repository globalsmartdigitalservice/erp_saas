import {
  ArrowLeft,
  Building2,
  ChevronRight,
  CircleAlert,
  Loader2,
} from "lucide-react";
import { useTranslation } from "react-i18next";

import type { EmpresaDeUsuario } from "@/modules/seguridad/types/sesion.types";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";

type Props = {
  empresas: EmpresaDeUsuario[];
  /** El id de la que se está estaAbriendo, para marcar solo esa como ocupada. */
  eligiendo: string | null;
  error?: string | null;
  onElegir: (empresaId: string) => void;
  onVolver: () => void;
};

export function EmpresasDeUsuario({
  empresas,
  eligiendo,
  error,
  onElegir,
  onVolver,
}: Props) {
  const { t } = useTranslation();
  const ocupado = eligiendo !== null;

  return (
    <div className="space-y-5">
      <ul className="space-y-2">
        {empresas.map((empresa, indice) => {
          const estaAbriendo = eligiendo === empresa.empresaId;

          return (
            <li key={empresa.empresaId}>
              <Button
                type="button"
                variant="outline"
                autoFocus={indice === 0}
                disabled={ocupado}
                aria-busy={estaAbriendo || undefined}
                onClick={() => onElegir(empresa.empresaId)}
                className="group h-auto w-full justify-start gap-3 px-4 py-3 hover:border-primary/50"
              >
                <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Building2 aria-hidden="true" />
                </span>

                <span className="min-w-0 flex-1 text-left">
                  <span className="block truncate">{empresa.razonSocial}</span>
                  <Badge variant="secondary" className="mt-1 font-normal">
                    {empresa.esMatriz ? t("login.casaMatriz") : t("login.sucursal")}
                  </Badge>
                </span>

                {estaAbriendo ? (
                  <Loader2 aria-hidden="true" className="animate-spin text-primary" />
                ) : (
                  <ChevronRight
                    aria-hidden="true"
                    className="text-muted-foreground transition-transform group-hover:translate-x-0.5"
                  />
                )}
              </Button>
            </li>
          );
        })}
      </ul>

      {error && (
        <Alert variant="destructive" className="bg-destructive/5">
          <CircleAlert aria-hidden="true" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button
        type="button"
        variant="ghost"
        className="gap-2"
        disabled={ocupado}
        onClick={onVolver}
      >
        <ArrowLeft aria-hidden="true" />
        {t("login.volver")}
      </Button>
    </div>
  );
}
