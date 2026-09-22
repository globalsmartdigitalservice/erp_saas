import { useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";

import { DialogoCategoria } from "@/modules/entidades/components/categorias/DialogoCategoria";
import { TablaCategorias } from "@/modules/entidades/components/categorias/TablaCategorias";
import { CATEGORIAS_ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { CategoriaEntidad } from "@/modules/entidades/types/entidad.types";
import { PageHeader } from "@/shared/components/PageHeader";

export function CategoriasPage() {
  const { t } = useTranslation();

  const { data, loading, error, refetch } = useQuery<{
    categoriasEntidad: CategoriaEntidad[];
  }>(CATEGORIAS_ENTIDAD);

  return (
    <section className="space-y-4">
      <PageHeader
        title={t("categorias.titulo")}
        description={t("categorias.ayuda")}
        action={<DialogoCategoria />}
      />

      <TablaCategorias
        categorias={data?.categoriasEntidad ?? []}
        cargando={loading}
        error={error}
        onReintentar={() => refetch()}
      />
    </section>
  );
}
