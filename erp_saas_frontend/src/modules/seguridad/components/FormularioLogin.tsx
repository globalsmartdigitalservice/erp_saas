import { CircleAlert } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import {
  CREDENCIALES_VACIAS,
  type Credenciales,
} from "@/modules/seguridad/types/sesion.types";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";

type Props = {
  enviando: boolean;
  error?: string | null;
  onEnviar: (credenciales: Credenciales) => void;
};

const ID_ERROR = "login-error";

export function FormularioLogin({ enviando, error, onEnviar }: Props) {
  const { t } = useTranslation();
  const [datos, setDatos] = useState<Credenciales>(CREDENCIALES_VACIAS);

  const cambiar = (campo: keyof Credenciales, valor: string) =>
    setDatos((actual) => ({ ...actual, [campo]: valor }));

  const completo =
    datos.identificador.trim() !== "" && datos.password !== "";

  return (
    <form
      className="space-y-5"
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        if (completo && !enviando) {
          onEnviar({ ...datos, identificador: datos.identificador.trim() });
        }
      }}
    >
      <div className="space-y-1.5">
        <Label htmlFor="identificador" obligatorio>
          {t("login.identificador")}
        </Label>
        <Input
          id="identificador"
          
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          autoFocus
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? ID_ERROR : "identificador-ayuda"}
          value={datos.identificador}
          onChange={(e) => cambiar("identificador", e.target.value)}
        />
        <p id="identificador-ayuda" className="text-xs text-muted-foreground">
          {t("login.identificadorAyuda")}
        </p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password" obligatorio>
          {t("login.password")}
        </Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? ID_ERROR : undefined}
          value={datos.password}
          onChange={(e) => cambiar("password", e.target.value)}
        />
      </div>

      {error && (
        <Alert id={ID_ERROR} variant="destructive" className="bg-destructive/5">
          <CircleAlert aria-hidden="true" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" className="w-full" disabled={!completo || enviando}>
        {enviando ? t("login.entrando") : t("login.entrar")}
      </Button>
    </form>
  );
}
