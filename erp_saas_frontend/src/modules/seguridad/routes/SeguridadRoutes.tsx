import { Navigate, Route, Routes } from "react-router-dom";

import { AltaMiembroPage } from "@/modules/seguridad/pages/AltaMiembroPage";
import { ListaMiembrosPage } from "@/modules/seguridad/pages/ListaMiembrosPage";

export function SeguridadRoutes() {
  return (
    <Routes>
      <Route path="usuarios">
        <Route index element={<ListaMiembrosPage />} />
        <Route path="nuevo" element={<AltaMiembroPage />} />
      </Route>
      <Route path="*" element={<Navigate to="usuarios" replace />} />
    </Routes>
  );
}
