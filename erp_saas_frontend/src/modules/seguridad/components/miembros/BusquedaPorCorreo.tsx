import { Search } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";

const FORMA_DE_CORREO = /^[^\s@]+@[^\s@]+$/;

type Props = {
  buscando: boolean;
  onBuscar: (email: string) => void;
};

export function BusquedaPorCorreo({ buscando, onBuscar }: Props) {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const limpio = email.trim();
  const completo = FORMA_DE_CORREO.test(limpio);

  return (
    <form
      className="flex flex-col gap-3 sm:flex-row sm:items-end"
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        if (completo && !buscando) onBuscar(limpio);
      }}
    >
      <div className="flex-1 space-y-1.5">
        <Label htmlFor="correo-buscado" obligatorio>
          {t("miembros.correo")}
        </Label>
        <Input
          id="correo-buscado"
          type="email"
          autoComplete="off"
          autoFocus
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <Button type="submit" className="gap-2" disabled={!completo || buscando}>
        <Search size={16} aria-hidden="true" />
        {buscando ? t("miembros.buscandoCorreo") : t("miembros.buscarCorreo")}
      </Button>
    </form>
  );
}
