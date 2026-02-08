# ============================================================================
# Frontend Dockerfile — React + Vite (multi-stage)
# ============================================================================
# Stage 1: Build the React app
# Stage 2: Serve with nginx
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Build
# ---------------------------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependency files first for better layer caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build argument for API URL (baked into the static bundle at build time)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# Build the production bundle
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2 — Serve with nginx
# ---------------------------------------------------------------------------
FROM nginx:alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
