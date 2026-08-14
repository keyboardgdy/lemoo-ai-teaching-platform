# syntax=docker/dockerfile:1.18
FROM node:24.11.1-bookworm-slim@sha256:48abc13a19400ca3985071e287bd405a1d99306770eb81d61202fb6b65cf0b57 AS build

WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.2.2 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile --filter @lemoo/web...
COPY apps/web ./apps/web
RUN pnpm --filter @lemoo/web build

FROM golang:1.26.5-alpine3.23@sha256:622e56dbc11a8cfe87cafa2331e9a201877271cbff918af53d3be315f3da88cc AS caddy-build

WORKDIR /source
COPY docker/caddy/go.mod docker/caddy/go.sum docker/caddy/main.go ./
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w -buildid=" -o /out/caddy .

FROM alpine:3.23.5@sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40

ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="Lemoo Stage 1A Web" \
      org.opencontainers.image.description="Simulator-only synthetic workspace; production unsupported" \
      org.opencontainers.image.source="https://github.com/keyboardgdy/lemoo-ai-teaching-platform" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="Apache-2.0"

RUN apk upgrade --no-cache \
    && apk add --no-cache ca-certificates tzdata \
    && addgroup -S -g 10001 lemoo \
    && adduser -S -D -H -u 10001 -G lemoo lemoo \
    && install -d -o 10001 -g 10001 /config /data /srv
COPY --from=caddy-build /out/caddy /usr/bin/caddy
COPY --chown=10001:10001 docker/Caddyfile /etc/caddy/Caddyfile
COPY --from=build --chown=10001:10001 /workspace/apps/web/dist /srv
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "--quiet", "--tries=1", "--spider", "http://127.0.0.1:8080/healthz"]
ENTRYPOINT ["caddy"]
CMD ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
