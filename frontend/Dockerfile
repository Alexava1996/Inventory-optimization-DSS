FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build
FROM node:24-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
RUN groupadd --gid 10001 inventory && useradd --uid 10001 --gid inventory inventory
COPY --from=build --chown=inventory:inventory /app/.next/standalone ./
COPY --from=build --chown=inventory:inventory /app/.next/static ./.next/static
USER inventory
EXPOSE 3000
CMD ["node", "server.js"]
