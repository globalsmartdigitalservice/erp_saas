import { useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";

import { DialogoCategoria } from "@/modules/entidades/components/categorias/DialogoCategoria";
import { TablaCategorias } from "@/modules/entidades/components/categorias/TablaCategorias";
import { CATEGORIAS_ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { CategoriaEntidad } from "@/modules/entidades/types/entidad.types";


export function CategoriasPage() {
  const { t } = useTranslation();

  const { data, loading, error, refetch } = useQuery<{
    categoriasEntidad: CategoriaEntidad[];
  }>(CATEGORIAS_ENTIDAD);

  return (
    <section className="space-y-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-xl font-semibold">
            {t("categorias.titulo")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("categorias.ayuda")}
          </p>
        </div>

        <DialogoCategoria />
      </header>

      <TablaCategorias
        categorias={data?.categoriasEntidad ?? []}
        cargando={loading}
        error={Boolean(error)}
        onReintentar={() => refetch()}
      />
    </section>
  );
}
