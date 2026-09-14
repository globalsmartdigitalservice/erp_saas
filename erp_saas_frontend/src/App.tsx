import { ApolloProvider } from "@apollo/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";

import { client } from "@/config/apollo";
import { EntidadesRoutes } from "@/modules/entidades/routes/EntidadesRoutes";
import { LoginPage } from "@/modules/seguridad/pages/LoginPage";
import { TipologiasRoutes } from "@/modules/tipologias/routes/TipologiasRoutes";
import { AppShell } from "@/shared/components/layout/AppShell";
import { ProtectedRoute } from "@/shared/components/ProtectedRoute";
import { PreferenciasProvider } from "@/shared/preferencias";
import { SessionProvider } from "@/shared/session";


function App() {
  return (
    <ApolloProvider client={client}>
      <PreferenciasProvider>
        <BrowserRouter>
          <Toaster position="top-right" richColors />

          {/* Adentro del router: `<ProtectedRoute>` navega al login. */}
          <SessionProvider>
            <Routes>
              {/* Fuera del AppShell: el login no lleva menú ni encabezado. */}
              <Route path="/login" element={<LoginPage />} />

              <Route element={<ProtectedRoute />}>
                <Route element={<AppShell />}>
                  <Route path="/" element={<Navigate to="/entidades" replace />} />
                  <Route path="/entidades/*" element={<EntidadesRoutes />} />
                  <Route path="/configuracion/*" element={<TipologiasRoutes />} />
                </Route>
              </Route>

              <Route
                path="*"
                element={
                  <div className="flex min-h-screen items-center justify-center text-muted-foreground">
                    404
                  </div>
                }
              />
            </Routes>
          </SessionProvider>
        </BrowserRouter>
      </PreferenciasProvider>
    </ApolloProvider>
  );
}

export default App;
