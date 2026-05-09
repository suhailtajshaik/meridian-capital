FROM node:20-alpine

WORKDIR /app

# Install deps before copying source for better layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source
COPY . .

EXPOSE 5173

# --host 0.0.0.0 is required — Vite binds 127.0.0.1 by default inside
# the container, which would be unreachable via Docker port-forwarding.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
