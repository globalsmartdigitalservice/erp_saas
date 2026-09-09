import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: true,
    proxy: {
      // El backend del ERP corre en el 10000, no en el 8000.
      // Lo publica `erp-infraestructura/docker-compose.yml`.
      //
      // Se proxea en vez de apuntar directo para que el navegador vea
      // un solo origen: sin eso hace falta CORS en el backend, que hoy
      // no está configurado.
      "/graphql/": {
        target: "http://localhost:10000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
