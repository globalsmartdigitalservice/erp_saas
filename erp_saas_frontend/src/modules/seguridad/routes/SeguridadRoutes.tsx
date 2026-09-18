import { Navigate, Route, Routes } from "react-router-dom";

import { AltaMiembroPage } from "@/modules/seguridad/pages/AltaMiembroPage";
import { DetalleMiembroPage } from "@/modules/seguridad/pages/DetalleMiembroPage";
import { DetalleRolPage } from "@/modules/seguridad/pages/DetalleRolPage";
import { ListaMiembrosPage } from "@/modules/seguridad/pages/ListaMiembrosPage";
import { ListaRolesPage } from "@/modules/seguridad/pages/ListaRolesPage";

export function SeguridadRoutes() {
  return (
    <Routes>
      <Route path="usuarios">
        <Route index element={<ListaMiembrosPage />} />
        <Route path="nuevo" element={<AltaMiembroPage />} />
        <Route path=":id" element={<DetalleMiembroPage />} />
      </Route>
      <Route path="roles">
        <Route index element={<ListaRolesPage />} />
        <Route path=":id" element={<DetalleRolPage />} />
      </Route>
      <Route path="*" element={<Navigate to="usuarios" replace />} />
    </Routes>
  );
}
