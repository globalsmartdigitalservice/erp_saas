import { useQuery } from "@apollo/client";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/shared/components/ui/badge";
import {
  AGRUPADORES,
  TIPOLOGIAS,
} from "@/shared/graphql/tipologias.queries";
import {
  origenDe,
  type Agrupador,
  type Tipologia,
} from "@/shared/types/tipologia.types";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";


export function ListasPage() {
  const { t } = useTranslation();
  const [agrupador, setAgrupador] = useState<number | null>(null);

  const listas = useQuery<{ agrupadores: Agrupador[] }>(AGRUPADORES);

  const valores = useQuery<{ tipologias: Tipologia[] }>(TIPOLOGIAS, {
    variables: { agrupador },
    skip: agrupador === null,
  });

  const filas = valores.data?.tipologias ?? [];

  return (
    <section className="space-y-4">
      <header>
        <h1 className="font-heading text-xl font-semibold">
          {t("listas.titulo")}
        </h1>
        <p className="text-sm text-muted-foreground">{t("listas.ayuda")}</p>
      </header>

      <Select
        value={agrupador === null ? undefined : String(agrupador)}
        onValueChange={(valor) => setAgrupador(Number(valor))}
        disabled={listas.loading}
      >
        <SelectTrigger className="w-[280px]">
          <SelectValue
            placeholder={
              listas.loading ? t("comun.cargando") : t("listas.elegiLista")
            }
          />
        </SelectTrigger>
        <SelectContent>
          {(listas.data?.agrupadores ?? []).map((lista) => (
            <SelectItem key={lista.valor} value={String(lista.valor)}>
              {lista.nombre}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {agrupador !== null && (
        <div className="space-y-2">
          {valores.loading ? (
            <p className="text-sm text-muted-foreground">
              {t("comun.cargando")}
            </p>
          ) : filas.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {t("comun.sinDatos")}
            </p>
          ) : (
            <>
              <p className="text-sm text-muted-foreground">
              
                {t("listas.valores", { count: filas.length })}
              </p>

              <ul className="divide-y rounded-md border">
                {filas.map((fila) => (
                  <li
                    key={fila.id}
                    className="flex items-center gap-3 px-3 py-2 text-sm"
                  >
                    <span>{fila.nombre}</span>
                    {fila.abreviatura && (
                      <span className="text-muted-foreground">
                        ({fila.abreviatura})
                      </span>
                    )}
                    <Badge variant="secondary" className="ml-auto">
                      {t(`listas.${origenDe(fila)}`)}
                    </Badge>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </section>
  );
}
