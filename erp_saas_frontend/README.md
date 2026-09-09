# erp-frontend

El ERP que usan los clientes. Consume el GraphQL de `erp-backend`.

Nació como copia de `portaldatos-frontend` (mismo stack, ya probado en
producción) y se le sacó todo lo del SSO, que acá no aplica.

## Stack

React 19 · Vite · TypeScript · Apollo Client · Tailwind 4 · shadcn/ui ·
react-router · i18next

## Levantarlo

El backend tiene que estar corriendo en el puerto **10000**
(`erp-infraestructura/docker-compose.yml`).

```bash
npm install
npm run dev
```

`/graphql/` lo proxea Vite al backend, así el navegador ve un solo
origen y no hace falta CORS.

## Cómo está organizado

```
src/
  config/     apollo, i18next, entorno, preferencias del navegador
  modules/    una carpeta por módulo, con los MISMOS nombres que las
              apps del backend (tipologias, entidades, …)
  shared/     lo que usan todos: componentes de shadcn en components/ui,
              el marco de la app, los selectores, los textos
```

**Regla dentro de un módulo:** los componentes se agrupan por la
pantalla a la que pertenecen (`components/alta-cliente/…`), no todos
sueltos en `components/`. En el molde esa carpeta llegó a 23 archivos
planos y no se encontraba nada.

## Dos cosas provisionales, que se van con el login

Todavía no existe el módulo 12 (usuarios y seguridad), así que:

- **La empresa y el idioma se eligen a mano**, con los dos combos de
  arriba a la derecha, y viajan en las cabeceras `X-Empresa-Id` y
  `X-Idioma`. Cuando haya login salen del token y los combos se borran.
- **El menú está escrito a mano** en `shared/components/AppShell.tsx`.
  Según ARQUITECTURA §12.2 tiene que armarse con lo que cada cliente
  tiene contratado, y eso vive en el módulo 25.

Los dos lugares tienen el comentario puesto.

## El multiidioma son dos mitades

| Mitad | Qué traduce | Dónde vive |
|---|---|---|
| Interfaz | "Guardar", los títulos | `src/shared/i18n/*.json` (i18next) |
| Datos | "Comercio", "Mayorista" | tabla `Traduccion`, en el backend |

El selector de idioma cambia las dos con el mismo clic. Lo que nadie
tradujo se muestra como fue cargado — media pantalla traducida es lo
normal en un ERP, no un error.
