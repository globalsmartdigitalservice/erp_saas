import { useMutation } from "@apollo/client";
import { Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  ACTUALIZAR_CONTACTO,
  CREAR_CONTACTO,
} from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { ContactoEntidad } from "@/modules/entidades/types/entidad.types";
import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { SaveButton } from "@/shared/components/SaveButton";
import { SelectorDeTipologia } from "@/shared/components/SelectorDeTipologia";
import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { mensajeDeError } from "@/shared/lib/errores";
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";

export function DialogoContacto({
  entidadId,
  contacto,
}: {
  entidadId: string;
  contacto?: ContactoEntidad;
}) {
  const { t } = useTranslation();
  const [abierto, setAbierto] = useState(false);
  const edicion = contacto !== undefined;

  return (
    <Dialog open={abierto} onOpenChange={setAbierto}>
      <DialogTrigger asChild>
        {edicion ? (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground"
            aria-label={t("entidades.editarContacto")}
            title={t("entidades.editarContacto")}
          >
            <Pencil aria-hidden="true" />
          </Button>
        ) : (
          <Button variant="outline" size="sm" className="gap-2">
            <Plus aria-hidden="true" />
            {t("entidades.agregarContacto")}
          </Button>
        )}
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {edicion
              ? t("entidades.editarContacto")
              : t("entidades.agregarContacto")}
          </DialogTitle>
        </DialogHeader>

        <FormularioContacto
          entidadId={entidadId}
          contacto={contacto}
          onCerrar={() => setAbierto(false)}
        />
      </DialogContent>
    </Dialog>
  );
}

function FormularioContacto({
  entidadId,
  contacto,
  onCerrar,
}: {
  entidadId: string;
  contacto?: ContactoEntidad;
  onCerrar: () => void;
}) {
  const { t } = useTranslation();
  const edicion = contacto !== undefined;

  const [nombre, setNombre] = useState(contacto?.nombre ?? "");
  const [cargo, setCargo] = useState(contacto?.cargo ?? "");
  const [email, setEmail] = useState(contacto?.email ?? "");
  const [telefono, setTelefono] = useState(contacto?.telefono ?? "");
  const [estadoId, setEstadoId] = useState<string | null>(
    contacto?.estado?.id ?? null,
  );

  const [guardarContacto, { loading, error }] = useMutation(
    edicion ? ACTUALIZAR_CONTACTO : CREAR_CONTACTO,
    { refetchQueries: [ENTIDAD] },
  );

  async function guardar() {
    const campos = {
      nombre: nombre.trim(),
      cargo: cargo.trim(),
      email: email.trim(),
      telefono: telefono.trim(),
      estadoId,
    };

    const resultado = await guardarContacto({
      variables: edicion
        ? { id: contacto.id, datos: campos }
        : { datos: { entidadId, ...campos } },
    });

    const guardado =
      resultado.data?.crearContactoEntidad ??
      resultado.data?.actualizarContactoEntidad;
    if (!guardado) return;

    toast.success(
      edicion
        ? t("entidades.contactoActualizado")
        : t("entidades.contactoAgregado"),
    );
    onCerrar();
  }

  const estaCompleto = nombre.trim() !== "" && estadoId !== null;

  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (estaCompleto && !loading) void guardar();
      }}
    >
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="nombreContacto" obligatorio>{t("entidades.nombre")}</Label>
            <Input
              id="nombreContacto"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cargo">{t("entidades.cargo")}</Label>
            <Input
              id="cargo"
              value={cargo}
              onChange={(e) => setCargo(e.target.value)}
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="email">{t("entidades.email")}</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="telefono">{t("entidades.telefono")}</Label>
            <Input
              id="telefono"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="contacto-estado" obligatorio>{t("entidades.estado")}</Label>
          <SelectorDeTipologia
            id="contacto-estado"
            codigo="ESTADO_REGISTRO"
            predeterminada={edicion ? undefined : ABREV_ACTIVO}
            valor={estadoId}
            onCambiar={setEstadoId}
            placeholder={t("entidades.elegiEstado")}
          />
        </div>

        <ErrorAlert message={mensajeDeError(error, t)} />
      </div>

      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onCerrar} disabled={loading}>
          {t("comun.cancelar")}
        </Button>
        <SaveButton isSaving={loading} disabled={!estaCompleto}>
          {t("entidades.guardar")}
        </SaveButton>
      </DialogFooter>
    </form>
  );
}
