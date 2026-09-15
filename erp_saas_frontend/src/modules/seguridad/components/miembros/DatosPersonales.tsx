import { useMutation } from "@apollo/client";
import { AtSign, KeyRound, Mail, Pencil, UserX } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { ACTUALIZAR_USUARIO } from "@/modules/seguridad/graphql/miembros.mutations";
import { DETALLE_MIEMBRO, MIEMBROS } from "@/modules/seguridad/graphql/miembros.queries";
import {
  iniciales,
  type CuentaDeMiembro,
} from "@/modules/seguridad/types/miembro.types";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { mensajeDeError } from "@/shared/lib/errores";

export function DatosPersonales({ cuenta }: { cuenta: CuentaDeMiembro }) {
  const { t } = useTranslation();
  const nombre = cuenta.nombreCompleto || cuenta.username;

  return (
    <Card>
      <CardContent className="flex flex-wrap items-center gap-4 pt-6">
        <Avatar className="size-14">
          <AvatarFallback className="bg-primary/10 text-lg font-semibold text-primary">
            {iniciales(nombre)}
          </AvatarFallback>
        </Avatar>

        <div className="min-w-0 flex-1 space-y-1">
          <h1 className="truncate font-heading text-xl font-semibold">{nombre}</h1>
          <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <AtSign size={14} aria-hidden="true" />
              {cuenta.username}
            </span>
            <span className="flex items-center gap-1.5">
              <Mail size={14} aria-hidden="true" />
              {cuenta.email}
            </span>
          </p>
          {(!cuenta.isActive || cuenta.debeCambiarPassword) && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {!cuenta.isActive && (
                <Badge variant="outline" className="gap-1 font-normal text-muted-foreground">
                  <UserX className="size-3" aria-hidden="true" />
                  {t("miembros.cuentaDesactivada")}
                </Badge>
              )}
              {cuenta.debeCambiarPassword && (
                <Badge variant="outline" className="gap-1 font-normal text-muted-foreground">
                  <KeyRound className="size-3" aria-hidden="true" />
                  {t("miembros.passwordTemporal")}
                </Badge>
              )}
            </div>
          )}
        </div>

        <DialogoDatosPersonales cuenta={cuenta} />
      </CardContent>
    </Card>
  );
}

function DialogoDatosPersonales({ cuenta }: { cuenta: CuentaDeMiembro }) {
  const { t } = useTranslation();
  const [abierto, setAbierto] = useState(false);

  return (
    <Dialog open={abierto} onOpenChange={setAbierto}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Pencil size={14} aria-hidden="true" />
          {t("miembros.editarDatos")}
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("miembros.editarDatos")}</DialogTitle>
          <DialogDescription>{t("miembros.editarDatosAyuda")}</DialogDescription>
        </DialogHeader>

        <FormularioDatosPersonales cuenta={cuenta} onCerrar={() => setAbierto(false)} />
      </DialogContent>
    </Dialog>
  );
}

function FormularioDatosPersonales({
  cuenta,
  onCerrar,
}: {
  cuenta: CuentaDeMiembro;
  onCerrar: () => void;
}) {
  const { t } = useTranslation();
  const [email, setEmail] = useState(cuenta.email);
  const [firstName, setFirstName] = useState(cuenta.firstName);
  const [lastName, setLastName] = useState(cuenta.lastName);
  const [segApellido, setSegApellido] = useState(cuenta.segApellido);

  const [actualizar, { loading, error }] = useMutation(ACTUALIZAR_USUARIO, {
    refetchQueries: [DETALLE_MIEMBRO, MIEMBROS],
  });

  async function guardar() {
    const resultado = await actualizar({
      variables: {
        id: cuenta.id,
        datos: {
          email: email.trim(),
          firstName: firstName.trim(),
          lastName: lastName.trim(),
          segApellido: segApellido.trim(),
        },
      },
    });
    if (!resultado.data?.actualizarUsuario) return;

    toast.success(t("miembros.datosGuardados"));
    onCerrar();
  }

  return (
    <>
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email-ficha" obligatorio>
            {t("miembros.correo")}
          </Label>
          <Input
            id="email-ficha"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="first-name-ficha">{t("miembros.nombre")}</Label>
            <Input
              id="first-name-ficha"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="last-name-ficha">{t("miembros.apellido")}</Label>
            <Input
              id="last-name-ficha"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="seg-apellido-ficha">{t("miembros.segApellido")}</Label>
            <Input
              id="seg-apellido-ficha"
              value={segApellido}
              onChange={(e) => setSegApellido(e.target.value)}
            />
          </div>
        </div>

        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {mensajeDeError(error, t)}
          </p>
        )}
      </div>

      <DialogFooter>
        <Button variant="ghost" onClick={onCerrar} disabled={loading}>
          {t("comun.cancelar")}
        </Button>
        <Button onClick={guardar} disabled={loading || email.trim() === ""}>
          {loading ? t("comun.cargando") : t("miembros.guardar")}
        </Button>
      </DialogFooter>
    </>
  );
}
