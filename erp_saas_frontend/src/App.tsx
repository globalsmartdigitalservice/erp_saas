import { ApolloProvider } from "@apollo/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";

import { client } from "@/config/apollo";
import { EntidadesRoutes } from "@/modules/entidades/routes/EntidadesRoutes";
import { TipologiasRoutes } from "@/modules/tipologias/routes/TipologiasRoutes";
import { AppShell } from "@/shared/components/layout/AppShell";
import { PreferenciasProvider } from "@/shared/preferencias";


function App() {
  return (
    <ApolloProvider client={client}>
      <PreferenciasProvider>
        <BrowserRouter>
          <Toaster position="top-right" richColors />

          <Routes>
            <Route element={<AppShell />}>
              <Route path="/" element={<Navigate to="/entidades" replace />} />
              <Route path="/entidades/*" element={<EntidadesRoutes />} />
              <Route path="/configuracion/*" element={<TipologiasRoutes />} />
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
        </BrowserRouter>
      </PreferenciasProvider>
    </ApolloProvider>
  );
}

export default App;
