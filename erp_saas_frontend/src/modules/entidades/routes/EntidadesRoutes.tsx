import { Navigate, Route, Routes } from "react-router-dom";

import { AltaEntidadPage } from "@/modules/entidades/pages/AltaEntidadPage";
import { CategoriasPage } from "@/modules/entidades/pages/CategoriasPage";
import { DetalleEntidadPage } from "@/modules/entidades/pages/DetalleEntidadPage";
import { EdicionEntidadPage } from "@/modules/entidades/pages/EdicionEntidadPage";
import { ListaEntidadesPage } from "@/modules/entidades/pages/ListaEntidadesPage";


export function EntidadesRoutes() {
  return (
    <Routes>
      <Route index element={<ListaEntidadesPage />} />
      <Route path="nueva" element={<AltaEntidadPage />} />
      <Route path="categorias" element={<CategoriasPage />} />
      <Route path=":id" element={<DetalleEntidadPage />} />
      <Route path=":id/editar" element={<EdicionEntidadPage />} />
      <Route path="*" element={<Navigate to="." replace />} />
    </Routes>
  );
}
