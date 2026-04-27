# Stage 1 — build Angular
FROM node:20-alpine AS builder
WORKDIR /app
COPY ui/package*.json ./
RUN npm ci --prefer-offline
COPY ui/ .
RUN npm run build -- --configuration=production

# Stage 2 — serve with nginx
FROM nginx:1.27-alpine
COPY --from=builder /app/dist/ui/browser /usr/share/nginx/html
COPY docker/ui/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
