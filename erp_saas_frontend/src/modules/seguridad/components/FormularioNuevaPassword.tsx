import { CircleAlert } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import {
  CAMBIO_DE_PASSWORD_VACIO,
  type CambioDePassword,
} from "@/modules/seguridad/types/sesion.types";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";

type Props = {
  enviando: boolean;
  error?: string | null;
  onEnviar: (datos: CambioDePassword) => void;
};

const ID_ERROR = "nueva-password-error";
const ID_COINCIDENCIA = "confirmacion-ayuda";

export function FormularioNuevaPassword({ enviando, error, onEnviar }: Props) {
  const { t } = useTranslation();
  const [datos, setDatos] = useState<CambioDePassword>(CAMBIO_DE_PASSWORD_VACIO);
  const [confirmacion, setConfirmacion] = useState("");

  const cambiar = (campo: keyof CambioDePassword, valor: string) =>
    setDatos((actual) => ({ ...actual, [campo]: valor }));

  const coinciden = confirmacion === datos.passwordNueva;
  const noCoinciden = confirmacion !== "" && !coinciden;
  const completo =
    datos.passwordActual !== "" && datos.passwordNueva !== "" && coinciden;

  return (
    <form
      className="space-y-5"
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        if (completo && !enviando) onEnviar(datos);
      }}
    >
      <div className="space-y-1.5">
        <Label htmlFor="password-actual" obligatorio>
          {t("nuevaPassword.actual")}
        </Label>
        <Input
          id="password-actual"
          type="password"
          autoComplete="current-password"
          autoFocus
          aria-describedby="password-actual-ayuda"
          value={datos.passwordActual}
          onChange={(e) => cambiar("passwordActual", e.target.value)}
        />
        <p id="password-actual-ayuda" className="text-xs text-muted-foreground">
          {t("nuevaPassword.actualAyuda")}
        </p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password-nueva" obligatorio>
          {t("nuevaPassword.nueva")}
        </Label>
        <Input
          id="password-nueva"
          type="password"
          autoComplete="new-password"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? ID_ERROR : undefined}
          value={datos.passwordNueva}
          onChange={(e) => cambiar("passwordNueva", e.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password-confirmacion" obligatorio>
          {t("nuevaPassword.confirmacion")}
        </Label>
        <Input
          id="password-confirmacion"
          type="password"
          autoComplete="new-password"
          aria-invalid={noCoinciden ? true : undefined}
          aria-describedby={noCoinciden ? ID_COINCIDENCIA : undefined}
          value={confirmacion}
          onChange={(e) => setConfirmacion(e.target.value)}
        />
        {noCoinciden && (
          <p id={ID_COINCIDENCIA} className="text-xs text-muted-foreground">
            {t("nuevaPassword.noCoinciden")}
          </p>
        )}
      </div>

      {error && (
        <Alert id={ID_ERROR} variant="destructive" className="bg-destructive/5">
          <CircleAlert aria-hidden="true" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" className="w-full" disabled={!completo || enviando}>
        {enviando ? t("nuevaPassword.guardando") : t("nuevaPassword.guardar")}
      </Button>
    </form>
  );
}
