import type { MutationResult } from "@apollo/client";
import { Loader2 } from "lucide-react";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { ErrorAlert } from "@/shared/components/ErrorAlert";
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
import { mensajeDeError } from "@/shared/lib/errores";
import { cn } from "@/shared/lib/utils";

type Props = {
  title: string;
  description: string;
  confirmLabel: string;
  /** El resultado de `useMutation`. */
  mutation: Pick<MutationResult<unknown>, "loading" | "error" | "reset">;
  /** Devolver `false` deja el diálogo abierto: la operación no se hizo. */
  onConfirm: () => Promise<boolean | void>;
  successMessage?: string;
  isDestructive?: boolean;
  children: ReactNode;
};

export function ConfirmDialog({
  title,
  description,
  confirmLabel,
  mutation,
  onConfirm,
  successMessage,
  isDestructive = false,
  children,
}: Props) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const { loading: isLoading, error, reset } = mutation;

  function close() {
    setIsOpen(false);
    reset();
  }

  return (
    <AlertDialog
      open={isOpen}
      onOpenChange={(open) => (open ? setIsOpen(true) : close())}
    >
      <AlertDialogTrigger asChild>{children}</AlertDialogTrigger>

      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>

        <ErrorAlert message={mensajeDeError(error, t)} />

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>
            {t("comun.cancelar")}
          </AlertDialogCancel>

          <AlertDialogAction
            disabled={isLoading}
            aria-busy={isLoading || undefined}
            className={cn(
              "gap-2",
              isDestructive && buttonVariants({ variant: "destructive" }),
            )}
            onClick={async (event) => {
              // Sin esto el diálogo se cierra antes de saber si salió bien.
              event.preventDefault();

              // Sin backend la mutation lanza: el error ya queda en `mutation`.
              try {
                if ((await onConfirm()) === false) return;
              } catch {
                return;
              }

              if (successMessage) toast.success(successMessage);
              close();
            }}
          >
            {isLoading && <Loader2 aria-hidden="true" className="size-4 animate-spin" />}
            {isLoading ? t("comun.cargando") : confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
