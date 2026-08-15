FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies reproducibly
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . .

# Build argument for Vite API Base URL (defaults to localhost:8000 or set to LAN IP at build time)
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build Vite static assets
RUN npm run build

# Runtime Stage
FROM node:20-alpine AS runner

WORKDIR /app

# Install simple, lightweight static file server
RUN npm install -g serve

# Copy compiled static distribution files
COPY --from=builder /app/dist ./dist

EXPOSE 3000

# Serve SPA static assets on port 3000
CMD ["serve", "-s", "dist", "-l", "3000", "--single"]
