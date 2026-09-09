import { useMutation } from "@apollo/client";
import { Ban } from "lucide-react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { Dato } from "@/modules/entidades/components/detalle/DatosGenerales";
import { DialogoContacto } from "@/modules/entidades/components/detalle/DialogoContacto";
import { DESACTIVAR_CONTACTO } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { ContactoEntidad } from "@/modules/entidades/types/entidad.types";
import { DialogoConfirmar } from "@/shared/components/DialogoConfirmar";
import { mensajeDeError } from "@/shared/lib/errores";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
} from "@/shared/components/ui/card";


export function ContactosDeEntidad({
  entidadId,
  contactos,
}: {
  entidadId: string;
  contactos: ContactoEntidad[];
}) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-end">
        <DialogoContacto entidadId={entidadId} />
      </CardHeader>

      <CardContent>
        {contactos.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("entidades.sinContactos")}
          </p>
        ) : (
          <ul className="divide-y">
            {contactos.map((contacto) => (
              <li
                key={contacto.id}
                className="flex items-start gap-2 py-3 first:pt-0 last:pb-0"
              >
                <div className="grid flex-1 gap-4 sm:grid-cols-5">
                  <Dato etiqueta={t("entidades.nombre")}>
                    {contacto.nombre}
                  </Dato>
                  <Dato etiqueta={t("entidades.cargo")}>{contacto.cargo}</Dato>
                  <Dato etiqueta={t("entidades.email")}>{contacto.email}</Dato>
                  <Dato etiqueta={t("entidades.telefono")}>
                    {contacto.telefono}
                  </Dato>
                  <Dato etiqueta={t("entidades.estado")}>
                    {contacto.estado?.nombre}
                  </Dato>
                </div>

                <div className="flex shrink-0 items-start">
                  <DialogoContacto entidadId={entidadId} contacto={contacto} />
                  <BajaDeContacto contacto={contacto} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}


function BajaDeContacto({ contacto }: { contacto: ContactoEntidad }) {
  const { t } = useTranslation();

  const [desactivar, { loading, error, reset }] = useMutation(
    DESACTIVAR_CONTACTO,
    { refetchQueries: [ENTIDAD] },
  );

  return (
    <DialogoConfirmar
      titulo={t("entidades.bajaContactoTitulo", {
        nombre: contacto.nombre,
      })}
      descripcion={t("entidades.bajaContactoAyuda")}
      etiquetaConfirmar={t("entidades.darDeBaja")}
      cargando={loading}
      error={mensajeDeError(error, t)}
      alCerrar={reset}
      onConfirmar={async () => {
        const resultado = await desactivar({ variables: { id: contacto.id } });

        if (!resultado.data?.desactivarContactoEntidad) return false;

        toast.success(t("entidades.contactoDadoDeBaja"));
      }}
    >
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 shrink-0 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        title={t("entidades.darDeBaja")}
      >
        <Ban size={15} />
        <span className="sr-only">{t("entidades.darDeBaja")}</span>
      </Button>
    </DialogoConfirmar>
  );
}
