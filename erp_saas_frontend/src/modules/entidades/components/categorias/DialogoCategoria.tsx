import { useMutation } from "@apollo/client";
import { Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  ACTUALIZAR_CATEGORIA,
  CREAR_CATEGORIA,
} from "@/modules/entidades/graphql/entidades.mutations";
import { CATEGORIAS_ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { CategoriaEntidad } from "@/modules/entidades/types/entidad.types";
import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { SaveButton } from "@/shared/components/SaveButton";
import { SelectorDeTipologia } from "@/shared/components/SelectorDeTipologia";
import { Button } from "@/shared/components/ui/button";
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
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";

export function DialogoCategoria({
  categoria,
}: {
  categoria?: CategoriaEntidad;
}) {
  const { t } = useTranslation();
  const [abierto, setAbierto] = useState(false);
  const edicion = categoria !== undefined;

  return (
    <Dialog open={abierto} onOpenChange={setAbierto}>
      <DialogTrigger asChild>
        {edicion ? (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            aria-label={t("categorias.editar")}
            title={t("categorias.editar")}
          >
            <Pencil aria-hidden="true" />
          </Button>
        ) : (
          <Button className="gap-2">
            <Plus aria-hidden="true" />
            {t("categorias.nueva")}
          </Button>
        )}
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {edicion ? t("categorias.editar") : t("categorias.nueva")}
          </DialogTitle>
          <DialogDescription>{t("categorias.ayudaDialogo")}</DialogDescription>
        </DialogHeader>

        <FormularioCategoria
          categoria={categoria}
          onCerrar={() => setAbierto(false)}
        />
      </DialogContent>
    </Dialog>
  );
}

function FormularioCategoria({
  categoria,
  onCerrar,
}: {
  categoria?: CategoriaEntidad;
  onCerrar: () => void;
}) {
  const { t } = useTranslation();
  const edicion = categoria !== undefined;

  const [nombre, setNombre] = useState(categoria?.nombre ?? "");
  const [descripcion, setDescripcion] = useState(categoria?.descripcion ?? "");
  const [descuento, setDescuento] = useState(
    categoria?.descuentoCategCliente ?? "",
  );
  const [estadoId, setEstadoId] = useState<string | null>(
    categoria?.estado?.id ?? null,
  );

  const [guardarCategoria, { loading, error }] = useMutation(
    edicion ? ACTUALIZAR_CATEGORIA : CREAR_CATEGORIA,
    { refetchQueries: [CATEGORIAS_ENTIDAD] },
  );

  async function guardar() {
    const datos = {
      nombre: nombre.trim(),
      descripcion: descripcion.trim(),

      descuentoCategCliente: descuento.trim() === "" ? "0" : descuento.trim(),
      estadoId,
    };

    const resultado = await guardarCategoria({
      variables: edicion ? { id: categoria.id, datos } : { datos },
    });

    const guardado =
      resultado.data?.crearCategoriaEntidad ??
      resultado.data?.actualizarCategoriaEntidad;
    if (!guardado) return;

    toast.success(edicion ? t("categorias.guardada") : t("categorias.creada"));
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
        <div className="space-y-1.5">
          <Label htmlFor="nombre" obligatorio>{t("categorias.nombre")}</Label>
          <Input
            id="nombre"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder={t("categorias.nombreEjemplo")}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="descripcion">{t("categorias.descripcion")}</Label>
          <Input
            id="descripcion"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="categoria-estado" obligatorio>{t("categorias.estado")}</Label>
          <SelectorDeTipologia
            id="categoria-estado"
            codigo="ESTADO_REGISTRO"
            predeterminada={edicion ? undefined : ABREV_ACTIVO}
            valor={estadoId}
            onCambiar={setEstadoId}
            placeholder={t("categorias.elegiEstado")}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="descuento">{t("categorias.descuento")}</Label>
          <Input
            id="descuento"
            inputMode="decimal"
            value={descuento}
            onChange={(e) => setDescuento(e.target.value)}
            placeholder="0.00"
            className="max-w-[140px]"
          />
          <p className="text-xs text-muted-foreground">
            {t("categorias.descuentoAyuda")}
          </p>
        </div>

        <ErrorAlert message={mensajeDeError(error, t)} />
      </div>

      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onCerrar} disabled={loading}>
          {t("comun.cancelar")}
        </Button>
        <SaveButton isSaving={loading} disabled={!estaCompleto}>
          {t("categorias.guardar")}
        </SaveButton>
      </DialogFooter>
    </form>
  );
}
