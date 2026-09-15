import { useMutation } from "@apollo/client";
import { LogOut } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate } from "react-router-dom";

import { AccesoLayout } from "@/modules/seguridad/components/AccesoLayout";
import { FormularioNuevaPassword } from "@/modules/seguridad/components/FormularioNuevaPassword";
import { CAMBIAR_MI_PASSWORD } from "@/modules/seguridad/graphql/seguridad.mutations";
import type { CambioDePassword } from "@/modules/seguridad/types/sesion.types";
import { Button } from "@/shared/components/ui/button";
import { mensajeDeError } from "@/shared/lib/errores";
import { useSession } from "@/shared/session";

export function NuevaPasswordPage() {
  const { t } = useTranslation();
  const { usuario, refrescar, logout } = useSession();
  const [guardando, setGuardando] = useState(false);
  const [saliendo, setSaliendo] = useState(false);

  const [cambiarMiPassword, cambio] = useMutation<{ cambiarMiPassword: boolean }>(
    CAMBIAR_MI_PASSWORD,
  );

  if (!usuario?.debeCambiarPassword) {
    return <Navigate to="/" replace />;
  }

  async function guardar(datos: CambioDePassword) {
    setGuardando(true);
    const resultado = await cambiarMiPassword({ variables: { datos } });

    if (!resultado.data?.cambiarMiPassword) {
      setGuardando(false);
      return;
    }

    await refrescar();
  }

  async function salir() {
    setSaliendo(true);
    await logout();
  }

  return (
    <AccesoLayout titulo={t("nuevaPassword.titulo")} ayuda={t("nuevaPassword.ayuda")}>
      <div className="space-y-4">
        <FormularioNuevaPassword
          enviando={cambio.loading || guardando}
          error={mensajeDeError(cambio.error, t)}
          onEnviar={guardar}
        />

        <Button
          type="button"
          variant="ghost"
          className="w-full gap-2"
          disabled={guardando || saliendo}
          onClick={salir}
        >
          <LogOut aria-hidden="true" />
          {t("nuevaPassword.salir")}
        </Button>
      </div>
    </AccesoLayout>
  );
}
