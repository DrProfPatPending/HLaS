FROM node:20-alpine AS build

# Upgrade npm to v11.12.0 (latest recommended)
RUN npm install -g npm@11.12.0

WORKDIR /app


# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy the rest of the frontend source
COPY frontend ./

# Set backend URL for Vite build
ARG VITE_APP_BACKEND_URL=/api
ENV VITE_APP_BACKEND_URL=${VITE_APP_BACKEND_URL}

# Build using Vite
RUN npm run build

FROM nginx:1.27-alpine

COPY deploy/nginx/frontend.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
