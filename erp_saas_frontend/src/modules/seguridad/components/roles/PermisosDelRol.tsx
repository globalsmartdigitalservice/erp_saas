import { useMutation, useQuery, type ApolloCache } from "@apollo/client";
import { KeySquare, Lock, Search, ShieldOff } from "lucide-react";
import { memo, useCallback, useDeferredValue, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  AGREGAR_PERMISO_AL_ROL,
  QUITAR_PERMISO_DEL_ROL,
} from "@/modules/seguridad/graphql/roles.mutations";
import {
  CATALOGO_DE_PERMISOS,
  PERMISOS_DEL_ROL,
} from "@/modules/seguridad/graphql/roles.queries";
import {
  codenameDe,
  grupoDePermiso,
  type PermisoDeCatalogo,
  type PermisoDelRol as LineaDePermiso,
} from "@/modules/seguridad/types/rol.types";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/shared/components/ui/accordion";
import { Badge } from "@/shared/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { Checkbox } from "@/shared/components/ui/checkbox";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Skeleton } from "@/shared/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/shared/components/ui/tooltip";
import { mensajeDeError } from "@/shared/lib/errores";

type Props = {
  rolId: string;
  esHeredado: boolean;
};

type PermisoVisible = PermisoDeCatalogo & {
  marcado: boolean;
  fueraDeAlcance: boolean;
};

type GrupoDePermisos = {
  clave: string;
  permisos: PermisoVisible[];
  marcados: number;
};

export function PermisosDelRol({ rolId, esHeredado }: Props) {
  const { t } = useTranslation();
  const [texto, setTexto] = useState("");
  const [abiertos, setAbiertos] = useState<string[] | null>(null);
  const [enCurso, setEnCurso] = useState<ReadonlySet<string>>(new Set());

  const asignados = useQuery<{ permisosDelRol: LineaDePermiso[] }>(PERMISOS_DEL_ROL, {
    variables: { rolId },
  });
  const catalogo = useQuery<{ catalogoDePermisos: PermisoDeCatalogo[] }>(
    CATALOGO_DE_PERMISOS,
    { skip: esHeredado },
  );

  const lineas = useMemo(() => asignados.data?.permisosDelRol ?? [], [asignados.data]);
  const visibles = useMemo(
    () => unir(lineas, catalogo.data?.catalogoDePermisos ?? [], esHeredado),
    [lineas, catalogo.data, esHeredado],
  );

  const textoDiferido = useDeferredValue(texto);
  const buscando = textoDiferido.trim() !== "";
  const grupos = useMemo(
    () => agrupar(filtrar(visibles, textoDiferido)),
    [visibles, textoDiferido],
  );

  const escribirEnCache = useCallback(
    (cache: ApolloCache<unknown>, lineasNuevas: LineaDePermiso[]) => {
      cache.writeQuery({
        query: PERMISOS_DEL_ROL,
        variables: { rolId },
        data: { permisosDelRol: lineasNuevas },
      });
      // El contador que muestra la lista de roles sale de otra consulta y
      // quedaría viejo al volver.
      cache.modify({
        id: cache.identify({ __typename: "Rol", id: rolId }),
        fields: { cantidadPermisos: () => lineasNuevas.length },
      });
    },
    [rolId],
  );

  const [agregar, agregado] = useMutation(AGREGAR_PERMISO_AL_ROL);
  const [quitar, quitado] = useMutation(QUITAR_PERMISO_DEL_ROL);

  const alternar = useCallback(
    async (authPermissionId: string, marcar: boolean) => {
      setEnCurso((previo) => new Set(previo).add(authPermissionId));
      try {
        const variables = { rolId, authPermissionId };
        if (marcar) {
          await agregar({
            variables,
            update: (cache, { data }) => {
              if (data) escribirEnCache(cache, data.agregarPermisoAlRol);
            },
          });
        } else {
          await quitar({
            variables,
            update: (cache, { data }) => {
              if (data) escribirEnCache(cache, data.quitarPermisoDelRol);
            },
          });
        }
      } catch {
        // El cartel de la tarjeta ya muestra el error que devolvió el servidor.
      } finally {
        setEnCurso((previo) => {
          const restantes = new Set(previo);
          restantes.delete(authPermissionId);
          return restantes;
        });
      }
    },
    [rolId, agregar, quitar, escribirEnCache],
  );

  const cargando = asignados.loading || catalogo.loading;
  const error = mensajeDeError(
    asignados.error ?? catalogo.error ?? agregado.error ?? quitado.error,
    t,
  );
  const abiertosVisibles = buscando
    ? grupos.map((grupo) => grupo.clave)
    : (abiertos ??
      grupos.filter((grupo) => grupo.marcados > 0).map((grupo) => grupo.clave));

  return (
    <Card>
      <CardHeader className="gap-4 space-y-0 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1.5">
          <CardTitle className="text-base">{t("roles.permisosTitulo")}</CardTitle>
          <CardDescription>
            {esHeredado ? t("roles.permisosAyudaHeredado") : t("roles.permisosAyuda")}
          </CardDescription>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-3">
          <span className="text-sm tabular-nums text-muted-foreground">
            {t("roles.permisosMarcados", { count: lineas.length })}
          </span>
          <div className="relative w-full sm:w-64">
            <Search
              className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              type="search"
              value={texto}
              onChange={(evento) => setTexto(evento.target.value)}
              placeholder={t("roles.buscarPermiso")}
              aria-label={t("roles.buscarPermiso")}
              className="pl-8"
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {error && (
          <p
            role="alert"
            className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive"
          >
            {error}
          </p>
        )}

        {cargando ? (
          <div className="space-y-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : grupos.length === 0 ? (
          <div className="flex items-start gap-3 rounded-md border border-dashed p-4">
            <ShieldOff
              className="mt-0.5 size-4 shrink-0 text-muted-foreground"
              aria-hidden="true"
            />
            <div>
              <p className="text-sm font-medium">
                {buscando ? t("roles.sinResultadosPermiso") : t("roles.sinPermisos")}
              </p>
              <p className="text-sm text-muted-foreground">
                {buscando
                  ? t("roles.sinResultadosPermisoAyuda")
                  : esHeredado
                    ? t("roles.sinPermisosHeredadoAyuda")
                    : t("roles.sinPermisosAyuda")}
              </p>
            </div>
          </div>
        ) : (
          <Accordion
            type="multiple"
            value={abiertosVisibles}
            onValueChange={buscando ? undefined : setAbiertos}
            className="rounded-md border"
          >
            {grupos.map((grupo) => (
              <GrupoDePermiso
                key={grupo.clave}
                grupo={grupo}
                editable={!esHeredado}
                enCurso={enCurso}
                onAlternar={alternar}
              />
            ))}
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
}

function GrupoDePermiso({
  grupo,
  editable,
  enCurso,
  onAlternar,
}: {
  grupo: GrupoDePermisos;
  editable: boolean;
  enCurso: ReadonlySet<string>;
  onAlternar: (authPermissionId: string, marcar: boolean) => void;
}) {
  const { t } = useTranslation();

  return (
    <AccordionItem value={grupo.clave} className="border-b px-1 last:border-b-0">
      <AccordionTrigger className="px-3 hover:no-underline">
        <span className="flex flex-1 items-center gap-3 text-left">
          <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
            <KeySquare className="size-4" aria-hidden="true" />
          </span>
          <span className="font-medium">
            {t("roles.grupo." + grupo.clave, { defaultValue: grupo.clave })}
          </span>
          <Badge variant="outline" className="ml-auto mr-2 font-normal tabular-nums">
            {grupo.marcados} / {grupo.permisos.length}
          </Badge>
        </span>
      </AccordionTrigger>

      <AccordionContent className="px-3">
        <ul className="grid gap-2 pb-2 lg:grid-cols-2">
          {grupo.permisos.map((permiso) => (
            <FilaDePermiso
              key={permiso.authPermissionId}
              authPermissionId={permiso.authPermissionId}
              codigo={codenameDe(permiso)}
              etiqueta={permiso.etiqueta}
              marcado={permiso.marcado}
              fueraDeAlcance={permiso.fueraDeAlcance}
              editable={editable}
              guardando={enCurso.has(permiso.authPermissionId)}
              onAlternar={onAlternar}
            />
          ))}
        </ul>
      </AccordionContent>
    </AccordionItem>
  );
}

const FilaDePermiso = memo(function FilaDePermiso({
  authPermissionId,
  codigo,
  etiqueta,
  marcado,
  fueraDeAlcance,
  editable,
  guardando,
  onAlternar,
}: {
  authPermissionId: string;
  codigo: string;
  etiqueta: string;
  marcado: boolean;
  fueraDeAlcance: boolean;
  editable: boolean;
  guardando: boolean;
  onAlternar: (authPermissionId: string, marcar: boolean) => void;
}) {
  const { t } = useTranslation();
  const id = "permiso-" + authPermissionId;
  const bloqueado = !editable || fueraDeAlcance;

  return (
    <li>
      <Label
        htmlFor={id}
        className="flex items-start gap-3 rounded-md border px-3 py-2.5 font-normal leading-normal transition-colors has-[button[data-state=checked]]:border-primary has-[button[data-state=checked]]:bg-primary/5 has-[button:not(:disabled)]:cursor-pointer has-[button:not(:disabled)]:hover:bg-muted/50"
      >
        <Checkbox
          id={id}
          className="mt-0.5"
          checked={marcado}
          disabled={bloqueado || guardando}
          onCheckedChange={(valor) => onAlternar(authPermissionId, valor === true)}
        />
        <span className="min-w-0 flex-1">
          <span className="block truncate">{etiqueta}</span>
          <span className="block truncate text-xs text-muted-foreground">{codigo}</span>
        </span>
        {fueraDeAlcance && (
          <Tooltip>
            <TooltipTrigger asChild>
              <span tabIndex={0} className="mt-0.5 shrink-0 text-muted-foreground">
                <Lock className="size-3.5" aria-hidden="true" />
                <span className="sr-only">{t("roles.fueraDeAlcance")}</span>
              </span>
            </TooltipTrigger>
            <TooltipContent>{t("roles.fueraDeAlcanceAyuda")}</TooltipContent>
          </Tooltip>
        )}
      </Label>
    </li>
  );
});

/**
 * El catálogo llega recortado a lo que quien mira puede otorgar, así que un
 * permiso que el rol tiene y quien mira no puede dar no vendría en esa lista:
 * sin esto la pantalla mostraría el rol con menos permisos de los que tiene.
 */
function unir(
  lineas: LineaDePermiso[],
  catalogo: PermisoDeCatalogo[],
  esHeredado: boolean,
): PermisoVisible[] {
  const asignados = new Set(lineas.map((linea) => linea.authPermissionId));
  const otorgables = new Set(catalogo.map((permiso) => permiso.authPermissionId));

  const delCatalogo = catalogo.map((permiso) => ({
    ...permiso,
    marcado: asignados.has(permiso.authPermissionId),
    fueraDeAlcance: false,
  }));

  const ajenos = lineas
    .filter((linea) => !otorgables.has(linea.authPermissionId))
    .map((linea) => ({
      ...linea,
      pantalla: null,
      modulo: null,
      marcado: true,
      fueraDeAlcance: !esHeredado,
    }));

  return [...delCatalogo, ...ajenos];
}

function sinTildes(texto: string): string {
  return texto.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase();
}

function filtrar(permisos: PermisoVisible[], texto: string): PermisoVisible[] {
  const buscado = sinTildes(texto.trim());
  if (!buscado) return permisos;

  return permisos.filter(
    (permiso) =>
      sinTildes(permiso.etiqueta).includes(buscado) ||
      sinTildes(permiso.codigo).includes(buscado),
  );
}

function agrupar(permisos: PermisoVisible[]): GrupoDePermisos[] {
  const porClave = new Map<string, PermisoVisible[]>();

  for (const permiso of permisos) {
    const clave = grupoDePermiso(permiso);
    const existentes = porClave.get(clave);
    if (existentes) existentes.push(permiso);
    else porClave.set(clave, [permiso]);
  }

  return [...porClave.entries()]
    .map(([clave, delGrupo]) => ({
      clave,
      permisos: [...delGrupo].sort((uno, otro) =>
        uno.etiqueta.localeCompare(otro.etiqueta),
      ),
      marcados: delGrupo.filter((permiso) => permiso.marcado).length,
    }))
    .sort((uno, otro) => uno.clave.localeCompare(otro.clave));
}
