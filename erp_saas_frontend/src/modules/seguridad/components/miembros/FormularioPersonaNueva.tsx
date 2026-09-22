import { useState } from "react";
import { useTranslation } from "react-i18next";

import { SeleccionDeRoles } from "@/modules/seguridad/components/miembros/SeleccionDeRoles";
import type { DatosDePersonaNueva } from "@/modules/seguridad/types/miembro.types";
import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { PasswordInput } from "@/shared/components/PasswordInput";
import { SaveButton } from "@/shared/components/SaveButton";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/shared/components/ui/radio-group";

type ModoDePassword = "generar" | "escribir";

type Props = {
  email: string;
  guardando: boolean;
  error?: string;
  onGuardar: (persona: DatosDePersonaNueva, rolIds: string[]) => void;
};

export function FormularioPersonaNueva({ email, guardando, error, onGuardar }: Props) {
  const { t } = useTranslation();
  const [username, setUsername] = useState(() => email.split("@")[0]);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [segApellido, setSegApellido] = useState("");
  const [modo, setModo] = useState<ModoDePassword>("generar");
  const [password, setPassword] = useState("");
  const [rolIds, setRolIds] = useState<string[]>([]);

  const estaCompleto = username.trim() !== "" && (modo === "generar" || password !== "");

  return (
    <form
      className="space-y-6"
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        if (!estaCompleto || guardando) return;
        onGuardar(
          {
            username: username.trim(),
            email,
            firstName: firstName.trim(),
            lastName: lastName.trim(),
            segApellido: segApellido.trim(),
            password: modo === "escribir" ? password : null,
          },
          rolIds,
        );
      }}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="username" obligatorio>
            {t("miembros.usuario")}
          </Label>
          <Input
            id="username"
            autoComplete="off"
            autoCapitalize="none"
            spellCheck={false}
            aria-describedby="username-ayuda"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <p id="username-ayuda" className="text-xs text-muted-foreground">
            {t("miembros.usuarioAyuda")}
          </p>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email-nuevo">{t("miembros.correo")}</Label>
          <Input id="email-nuevo" type="email" value={email} disabled />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="first-name">{t("miembros.nombre")}</Label>
          <Input id="first-name" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="last-name">{t("miembros.apellido")}</Label>
          <Input id="last-name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="seg-apellido">{t("miembros.segApellido")}</Label>
          <Input
            id="seg-apellido"
            value={segApellido}
            onChange={(e) => setSegApellido(e.target.value)}
          />
        </div>
      </div>

      <fieldset className="space-y-2">
        <legend className="text-sm font-medium">{t("miembros.password")}</legend>
        <RadioGroup
          value={modo}
          onValueChange={(valor: string) => setModo(valor as ModoDePassword)}
          className="grid gap-2 sm:grid-cols-2"
        >
          <OpcionDePassword
            valor="generar"
            titulo={t("miembros.passwordGenerar")}
            ayuda={t("miembros.passwordGenerarAyuda")}
          />
          <OpcionDePassword
            valor="escribir"
            titulo={t("miembros.passwordEscribir")}
            ayuda={t("miembros.passwordEscribirAyuda")}
          />
        </RadioGroup>

        {modo === "escribir" && (
          <PasswordInput
            autoComplete="new-password"
            aria-label={t("miembros.password")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        )}
      </fieldset>

      <SeleccionDeRoles seleccionados={rolIds} onCambiar={setRolIds} />

      <ErrorAlert message={error} />

      <div className="flex justify-end">
        <SaveButton
          isSaving={guardando}
          savingText={t("miembros.dandoDeAlta")}
          disabled={!estaCompleto}
        >
          {t("miembros.darDeAlta")}
        </SaveButton>
      </div>
    </form>
  );
}

function OpcionDePassword({
  valor,
  titulo,
  ayuda,
}: {
  valor: ModoDePassword;
  titulo: string;
  ayuda: string;
}) {
  const id = `password-${valor}`;

  return (
    <Label
      htmlFor={id}
      className="flex cursor-pointer items-start gap-3 rounded-md border p-3 font-normal leading-normal transition-colors hover:bg-muted/50 has-[button[data-state=checked]]:border-primary has-[button[data-state=checked]]:bg-primary/5"
    >
      <RadioGroupItem value={valor} id={id} className="mt-0.5" />
      <span className="space-y-0.5">
        <span className="block text-sm font-medium">{titulo}</span>
        <span className="block text-xs text-muted-foreground">{ayuda}</span>
      </span>
    </Label>
  );
}
