FROM node:22.22.2-alpine AS build

WORKDIR /app


# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npx --yes npm@12.2.2 ci

# Copy the rest of the frontend source
COPY frontend ./

# Set backend URL for Vite build
ARG VITE_APP_BACKEND_URL=/api
ENV VITE_APP_BACKEND_URL=${VITE_APP_BACKEND_URL}

# Build using Vite
RUN npx --yes npm@12.2.2 run build

FROM nginx:1.30-alpine

COPY deploy/nginx/frontend.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
