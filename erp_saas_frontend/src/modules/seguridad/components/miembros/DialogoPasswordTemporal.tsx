import { Copy, KeyRound } from "lucide-react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";

type Props = {
  nombre: string;
  password: string;
  onCerrar: () => void;
};

export function DialogoPasswordTemporal({ nombre, password, onCerrar }: Props) {
  const { t } = useTranslation();

  async function copiar() {
    try {
      await navigator.clipboard.writeText(password);
      toast.success(t("miembros.copiada"));
    } catch {
      toast.error(t("miembros.noCopiada"));
    }
  }

  return (
    <Dialog open onOpenChange={(abierto) => !abierto && onCerrar()}>
      <DialogContent>
        <DialogHeader className="items-center text-center sm:text-center">
          <span className="mb-2 flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
            <KeyRound aria-hidden="true" />
          </span>
          <DialogTitle>{t("miembros.temporalTitulo")}</DialogTitle>
          <DialogDescription>{t("miembros.temporalAyuda", { nombre })}</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2 rounded-lg border bg-muted/40 py-2 pl-4 pr-2">
          <code className="flex-1 select-all font-mono text-lg tracking-wider">{password}</code>
          <Button type="button" variant="outline" size="sm" className="gap-2" onClick={copiar}>
            <Copy size={14} aria-hidden="true" />
            {t("miembros.copiar")}
          </Button>
        </div>

        <DialogFooter>
          <Button onClick={onCerrar}>{t("miembros.listo")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
