# ─── RADAR Frontend Dockerfile (multi-stage) ─────────────────────────────────
# Stage 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files and install dependencies (layer cached)
COPY package*.json ./
RUN npm ci --silent

# Copy source and build production bundle
COPY . .
RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Serve with Nginx
FROM nginx:1.27-alpine

# Remove default nginx site
RUN rm -rf /usr/share/nginx/html/*

# Copy built React app from builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy our custom Nginx config (handles API proxy + WebSocket + SPA routing)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
