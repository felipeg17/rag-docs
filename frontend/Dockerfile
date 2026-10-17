# Web UI: Vite build served by nginx-unprivileged, which also proxies /api to the backend.
# Build context: frontend/. API types are committed; the image never regenerates them.

FROM node:24-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.29-alpine
ENV NGINX_ENVSUBST_FILTER=^API_
COPY nginx/security-headers.conf /etc/nginx/security-headers.conf
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 8502
