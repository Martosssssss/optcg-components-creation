# Build del frontend React
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Servido estático con nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html