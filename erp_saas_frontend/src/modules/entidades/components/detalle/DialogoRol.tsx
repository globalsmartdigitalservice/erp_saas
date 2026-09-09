import { useMutation, useQuery } from "@apollo/client";
import { Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  ACTUALIZAR_ROL,
  CREAR_ROL,
} from "@/modules/entidades/graphql/entidades.mutations";
import {
  CATEGORIAS_ENTIDAD,
  ENTIDAD,
} from "@/modules/entidades/graphql/entidades.queries";
import type {
  CategoriaEntidad,
  RolEntidad,
} from "@/modules/entidades/types/entidad.types";
import { SelectorDeTipologia } from "@/shared/components/SelectorDeTipologia";
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";
import { Badge } from "@/shared/components/ui/badge";
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
import { mensajeDeError } from "@/shared/lib/errores";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";


export function DialogoRol({
  entidadId,
  rol,
}: {
  entidadId: string;
  rol?: RolEntidad;
}) {
  const { t } = useTranslation();
  const [abierto, setAbierto] = useState(false);
  const edicion = rol !== undefined;

  return (
    <Dialog open={abierto} onOpenChange={setAbierto}>
      <DialogTrigger asChild>
        {edicion ? (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground"
            title={t("entidades.editarRol")}
          >
            <Pencil size={15} />
            <span className="sr-only">{t("entidades.editarRol")}</span>
          </Button>
        ) : (
          <Button variant="outline" size="sm" className="gap-2">
            <Plus size={14} />
            {t("entidades.agregarRol")}
          </Button>
        )}
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {edicion ? t("entidades.editarRol") : t("entidades.agregarRol")}
          </DialogTitle>
        </DialogHeader>

        <FormularioRol
          entidadId={entidadId}
          rol={rol}
          onCerrar={() => setAbierto(false)}
        />
      </DialogContent>
    </Dialog>
  );
}

function FormularioRol({
  entidadId,
  rol,
  onCerrar,
}: {
  entidadId: string;
  rol?: RolEntidad;
  onCerrar: () => void;
}) {
  const { t } = useTranslation();
  const edicion = rol !== undefined;

  const [tipoRolId, setTipoRolId] = useState<string | null>(
    rol?.tipoRol?.id ?? null,
  );
  const [estadoId, setEstadoId] = useState<string | null>(
    rol?.estado?.id ?? null,
  );
  const [categoriaId, setCategoriaId] = useState<string | null>(
    rol?.categoria?.id ?? null,
  );
  const [limiteCredito, setLimiteCredito] = useState(rol?.limiteCredito ?? "");

 
  const categorias = useQuery<{ categoriasEntidad: CategoriaEntidad[] }>(
    CATEGORIAS_ENTIDAD,
  );

  const [guardarRol, { loading, error }] = useMutation(
    edicion ? ACTUALIZAR_ROL : CREAR_ROL,
    { refetchQueries: [ENTIDAD] },
  );

  async function guardar() {

    const limite = limiteCredito.trim() === "" ? null : limiteCredito.trim();

    const resultado = await guardarRol({
      variables: edicion
        ? {
            id: rol.id,
            datos: {
              estadoId,
              categoriaEntidadId: categoriaId,
              limiteCredito: limite,
            },
          }
        : {
            datos: {
              entidadId,
              tipoRolId,
              estadoId,
              categoriaEntidadId: categoriaId,
              limiteCredito: limite,
            },
          },
    });

    const guardado =
      resultado.data?.crearRolEntidad ?? resultado.data?.actualizarRolEntidad;
    if (!guardado) return;

    toast.success(
      edicion ? t("entidades.rolActualizado") : t("entidades.rolAgregado"),
    );
    onCerrar();
  }

  return (
    <>
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label obligatorio>{t("entidades.rol")}</Label>

          {edicion ? (
            <div className="space-y-1.5">
              <div>
                <Badge>{rol.tipoRol?.nombre ?? "—"}</Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                {t("entidades.tipoRolFijo")}
              </p>
            </div>
          ) : (
            <SelectorDeTipologia
              codigo="TIPO_ROL"
              valor={tipoRolId}
              onCambiar={setTipoRolId}
              placeholder={t("entidades.elegiRol")}
            />
          )}
        </div>

        <div className="space-y-1.5">
          <Label obligatorio>{t("entidades.estado")}</Label>
          <SelectorDeTipologia
            codigo="ESTADO_REGISTRO"
            predeterminada={edicion ? undefined : ABREV_ACTIVO}
            valor={estadoId}
            onCambiar={setEstadoId}
            placeholder={t("entidades.elegiEstado")}
          />
        </div>

        <div className="space-y-1.5">
          <Label>{t("entidades.categoria")}</Label>
          <Select
            value={categoriaId ?? undefined}
            onValueChange={setCategoriaId}
            disabled={
              categorias.loading ||
              (categorias.data?.categoriasEntidad.length ?? 0) === 0
            }
          >
            <SelectTrigger>
              <SelectValue placeholder={t("entidades.sinCategoria")} />
            </SelectTrigger>
            <SelectContent>
              {(categorias.data?.categoriasEntidad ?? []).map((categoria) => (
                <SelectItem key={categoria.id} value={categoria.id}>
                  {categoria.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="limite">{t("entidades.limiteCredito")}</Label>
          <Input
            id="limite"
            inputMode="decimal"
            value={limiteCredito}
            onChange={(e) => setLimiteCredito(e.target.value)}
            placeholder="0.00"
          />
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
        <Button
          onClick={guardar}
          disabled={
            loading || estadoId === null || (!edicion && tipoRolId === null)
          }
        >
          {loading ? t("comun.cargando") : t("entidades.guardar")}
        </Button>
      </DialogFooter>
    </>
  );
}
