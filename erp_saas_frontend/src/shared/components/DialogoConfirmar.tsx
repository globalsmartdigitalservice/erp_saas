import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/shared/components/ui/alert-dialog";
import { buttonVariants } from "@/shared/components/ui/button";
import { cn } from "@/shared/lib/utils";


export function DialogoConfirmar({
  titulo,
  descripcion,
  etiquetaConfirmar,
  onConfirmar,
  cargando = false,
  error,
  alCerrar,
  destructivo = false,
  children,
}: {
  titulo: string;
  descripcion: string;
  etiquetaConfirmar: string;

  onConfirmar: () => Promise<boolean | void>;
  cargando?: boolean;
  error?: string;

  alCerrar?: () => void;

  destructivo?: boolean;

  children: ReactNode;
}) {
  const { t } = useTranslation();
  const [abierto, setAbierto] = useState(false);

  return (
    <AlertDialog
      open={abierto}
      onOpenChange={(valor) => {
        setAbierto(valor);
        if (!valor) alCerrar?.();
      }}
    >
      <AlertDialogTrigger asChild>{children}</AlertDialogTrigger>

      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{titulo}</AlertDialogTitle>
          <AlertDialogDescription>{descripcion}</AlertDialogDescription>
        </AlertDialogHeader>

        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel disabled={cargando}>
            {t("comun.cancelar")}
          </AlertDialogCancel>

          <AlertDialogAction
            disabled={cargando}
            className={cn(
              destructivo && buttonVariants({ variant: "destructive" }),
            )}
            onClick={async (evento) => {
         
              evento.preventDefault();

              const resultado = await onConfirmar();
              if (resultado === false) return;

              setAbierto(false);
              alCerrar?.();
            }}
          >
            {cargando ? t("comun.cargando") : etiquetaConfirmar}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
