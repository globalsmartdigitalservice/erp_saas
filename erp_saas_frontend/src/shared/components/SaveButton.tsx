import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { Button, type ButtonProps } from "@/shared/components/ui/button";

type Props = Omit<ButtonProps, "type" | "children"> & {
  isSaving: boolean;
  /** Lo que dice mientras espera, si no es "Guardando…". */
  savingText?: string;
  children: ReactNode;
};

/** El botón de envío de un formulario: mientras guarda, gira y dice "Guardando…". */
export function SaveButton({
  isSaving,
  savingText,
  disabled,
  children,
  ...props
}: Props) {
  const { t } = useTranslation();

  return (
    <Button
      type="submit"
      disabled={disabled || isSaving}
      aria-busy={isSaving || undefined}
      {...props}
    >
      {isSaving && <Loader2 aria-hidden="true" className="animate-spin" />}
      {isSaving ? (savingText ?? t("comun.guardando")) : children}
    </Button>
  );
}
