import { useMutation } from "@apollo/client";
import { Ban, Contact } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Dato } from "@/modules/entidades/components/detalle/DatosGenerales";
import { DialogoContacto } from "@/modules/entidades/components/detalle/DialogoContacto";
import { DESACTIVAR_CONTACTO } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { ContactoEntidad } from "@/modules/entidades/types/entidad.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { EmptyState } from "@/shared/components/TableStates";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader } from "@/shared/components/ui/card";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";

const ENLACE = "text-primary underline-offset-4 hover:underline";

export function ContactosDeEntidad({
  entidadId,
  contactos,
}: {
  entidadId: string;
  contactos: ContactoEntidad[];
}) {
  const { t } = useTranslation();
  const activoId = useEstadoActivoId();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-end space-y-0">
        <DialogoContacto entidadId={entidadId} />
      </CardHeader>

      <CardContent>
        {contactos.length === 0 ? (
          <EmptyState icon={Contact} title={t("entidades.sinContactos")} />
        ) : (
          <ul className="divide-y">
            {contactos.map((contacto) => (
              <li
                key={contacto.id}
                className="flex items-start gap-2 py-3 first:pt-0 last:pb-0"
              >
                <div className="grid min-w-0 flex-1 gap-4 sm:grid-cols-5">
                  <Dato etiqueta={t("entidades.nombre")}>
                    {contacto.nombre}
                  </Dato>
                  <Dato etiqueta={t("entidades.cargo")}>{contacto.cargo}</Dato>
                  <Dato etiqueta={t("entidades.email")}>
                    {contacto.email && (
                      <a href={`mailto:${contacto.email}`} className={ENLACE}>
                        {contacto.email}
                      </a>
                    )}
                  </Dato>
                  <Dato etiqueta={t("entidades.telefono")}>
                    {contacto.telefono && (
                      <a href={`tel:${contacto.telefono}`} className={ENLACE}>
                        {contacto.telefono}
                      </a>
                    )}
                  </Dato>
                  <Dato etiqueta={t("entidades.estado")}>
                    <BadgeDeEstado estado={contacto.estado} activoId={activoId} />
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

  const [desactivar, mutacion] = useMutation(
    DESACTIVAR_CONTACTO,
    { refetchQueries: [ENTIDAD] },
  );

  return (
    <ConfirmDialog
      title={t("entidades.bajaContactoTitulo", {
        nombre: contacto.nombre,
      })}
      description={t("entidades.bajaContactoAyuda")}
      confirmLabel={t("entidades.darDeBaja")}
      mutation={mutacion}
      successMessage={t("entidades.contactoDadoDeBaja")}
      onConfirm={async () => {
        const resultado = await desactivar({ variables: { id: contacto.id } });

        if (!resultado.data?.desactivarContactoEntidad) return false;
      }}
    >
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 shrink-0 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        aria-label={t("entidades.darDeBaja")}
        title={t("entidades.darDeBaja")}
      >
        <Ban aria-hidden="true" />
      </Button>
    </ConfirmDialog>
  );
}
