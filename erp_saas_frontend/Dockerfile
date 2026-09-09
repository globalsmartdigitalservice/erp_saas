
# Etapa 1: Build
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL
ARG VITE_TURNSTILE_SITE_KEY

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_TURNSTILE_SITE_KEY=$VITE_TURNSTILE_SITE_KEY

RUN npx vite build

# Etapa 2: Producción con Nginx Unprivileged (Seguro y sin root)
FROM nginxinc/nginx-unprivileged:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

# Nginx unprivileged usa el puerto 8080 por defecto, no el 80
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]