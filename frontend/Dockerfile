FROM node:20-alpine AS build

# Upgrade npm to v11.12.0 (latest recommended)
RUN npm install -g npm@11.12.0

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./

ARG VUE_APP_BACKEND_URL=/api
ENV VUE_APP_BACKEND_URL=${VUE_APP_BACKEND_URL}

RUN node ./node_modules/@vue/cli-service/bin/vue-cli-service.js build

FROM nginx:1.27-alpine

COPY deploy/nginx/frontend.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
