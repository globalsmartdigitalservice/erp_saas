import { CircleAlert, Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  type Credenciales,
} from "@/modules/seguridad/types/sesion.types";
import { PasswordInput } from "@/shared/components/PasswordInput";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";

type Props = {
  /** Lo que se escribió antes de pasar al selector de empresas, al volver de él. */
  inicial: Credenciales | null;
  enviando: boolean;
  error?: string | null;
  onEnviar: (credenciales: Credenciales) => void;
  onEditar: () => void;
};

const ID_ERROR = "login-error";
const ID_AYUDA = "identificador-ayuda";

const DEV_USUARIO = "dev"
// const DEV_USUARIO = ""
const DEV_PASSWORD = "Dev2026**"
// const DEV_PASSWORD = ""

export function FormularioLogin({
  inicial,
  enviando,
  error,
  onEnviar,
  onEditar,
}: Props) {
  const { t } = useTranslation();
  // PROVISIONAL (desarrollo): el formulario arranca precargado.
  // Para volver atrás: descomentar la línea de abajo y borrar el useState que la sigue.
  // const [datos, setDatos] = useState<Credenciales>(inicial ?? CREDENCIALES_VACIAS);
  const [datos, setDatos] = useState<Credenciales>(
    inicial ?? { identificador: DEV_USUARIO, password: DEV_PASSWORD },
  );
  const campoPassword = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!error || enviando) return;
    campoPassword.current?.focus();
    campoPassword.current?.select();
  }, [error, enviando]);

  const cambiar = (campo: keyof Credenciales, valor: string) => {
    setDatos((actual) => ({ ...actual, [campo]: valor }));
    if (error) onEditar();
  };

  const estaCompleto =
    datos.identificador.trim() !== "" && datos.password !== "";

  return (
    <form
      className="space-y-5"
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        if (estaCompleto && !enviando) {
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
          readOnly={enviando}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${ID_AYUDA} ${ID_ERROR}` : ID_AYUDA}
          value={datos.identificador}
          onChange={(e) => cambiar("identificador", e.target.value)}
        />
        <p id={ID_AYUDA} className="text-xs text-muted-foreground">
          {t("login.identificadorAyuda")}
        </p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password" obligatorio>
          {t("login.password")}
        </Label>
        <PasswordInput
          ref={campoPassword}
          id="password"
          autoComplete="current-password"
          readOnly={enviando}
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

      <div className="space-y-3">
        <Button
          type="submit"
          className="w-full"
          disabled={!estaCompleto || enviando}
          aria-busy={enviando || undefined}
        >
          {enviando && <Loader2 aria-hidden="true" className="animate-spin" />}
          {enviando ? t("login.entrando") : t("login.entrar")}
        </Button>

        <p className="text-center text-xs text-muted-foreground">
          {t("login.olvidoPassword")}
        </p>
      </div>
    </form>
  );
}
