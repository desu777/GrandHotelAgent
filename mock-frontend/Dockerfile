# Stage 1: Build
FROM node:22-alpine AS builder
WORKDIR /app

# Build args for Vite env injection (baked into static bundle)
# Default to localhost:8000 - browser needs to reach exposed Docker port
ARG VITE_AGENT_API_BASE_URL=http://localhost:8000
ARG VITE_AGENT_JWT
ARG VITE_LOG_LEVEL=debug

# Set as env for Vite build
ENV VITE_AGENT_API_BASE_URL=$VITE_AGENT_API_BASE_URL
ENV VITE_AGENT_JWT=$VITE_AGENT_JWT
ENV VITE_LOG_LEVEL=$VITE_LOG_LEVEL

# Install dependencies (npm install bo brak package-lock.json - user używa pnpm)
COPY package*.json ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
