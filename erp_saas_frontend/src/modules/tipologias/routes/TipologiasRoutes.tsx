import { Navigate, Route, Routes } from "react-router-dom";

import { ListasPage } from "@/modules/tipologias/pages/ListasPage";


export function TipologiasRoutes() {
  return (
    <Routes>
      <Route path="listas" element={<ListasPage />} />
      <Route path="*" element={<Navigate to="listas" replace />} />
    </Routes>
  );
}
