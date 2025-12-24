# MagoneAI Production Deployment Plan
## External API Access + Monitoring Stack

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Stack](#2-component-stack)
3. [Infrastructure Requirements](#3-infrastructure-requirements)
4. [Docker Compose Configuration](#4-docker-compose-configuration)
5. [API Gateway Configuration](#5-api-gateway-configuration)
6. [Monitoring Setup](#6-monitoring-setup)
7. [Deployment Steps](#7-deployment-steps)
8. [Security Considerations](#8-security-considerations)
9. [Scaling Guidelines](#9-scaling-guidelines)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Architecture Overview

```
                                    ┌─────────────────────────────────────┐
                                    │         EXTERNAL CLIENTS            │
                                    │   (Mobile Apps, Web Apps, APIs)     │
                                    └─────────────────┬───────────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   EDGE LAYER                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                         TRAEFIK (Reverse Proxy)                              │   │
│  │                    Ports: 80 (HTTP) → 443 (HTTPS)                            │   │
│  │                    TLS Termination, Let's Encrypt                            │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                            │
└────────────────────────────────────────┼────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────┼────────────────────────────────────────────┐
│                              API GATEWAY LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                              KONG GATEWAY                                    │   │
│  │                           Port: 8000 (Proxy)                                 │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │   │
│  │  │ Rate Limit  │ │  API Keys   │ │   JWT Auth  │ │   Logging   │           │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │   │
│  │  │   CORS      │ │  Metrics    │ │ Req Transform│ │  Caching    │           │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                            │
└────────────────────────────────────────┼────────────────────────────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│   MAGONEAI API  │           │    NEXT.JS UI   │           │   TEMPORAL UI   │
│   FastAPI:8080  │           │    Web:3000     │           │    UI:8081      │
│   (3 replicas)  │           │   (2 replicas)  │           │                 │
└────────┬────────┘           └─────────────────┘           └─────────────────┘
         │
         │  Temporal Task Queue
         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              WORKER LAYER                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                      TEMPORAL WORKERS (2-10 replicas)                        │   │
│  │                        Auto-scaling based on queue depth                      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
         │
         │  Data Layer Connections
         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               DATA LAYER                                             │
│                                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │  PostgreSQL   │  │    Redis      │  │    Qdrant     │  │   Temporal    │        │
│  │    (5432)     │  │    (6379)     │  │    (6333)     │  │    (7233)     │        │
│  │   Primary DB  │  │ Cache/Session │  │  Vector Store │  │  Workflow DB  │        │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘        │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
         │
         │  Metrics Collection
         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            MONITORING LAYER                                          │
│                                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │  Prometheus   │  │    Grafana    │  │    Loki       │  │  AlertManager │        │
│  │    (9090)     │  │    (3001)     │  │    (3100)     │  │    (9093)     │        │
│  │   Metrics     │  │  Dashboards   │  │     Logs      │  │    Alerts     │        │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘        │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Stack

| Layer | Component | Purpose | Port |
|-------|-----------|---------|------|
| **Edge** | Traefik | Reverse proxy, TLS, routing | 80, 443 |
| **Gateway** | Kong | API gateway, auth, rate limiting | 8000, 8001 |
| **Gateway DB** | Kong PostgreSQL | Kong configuration storage | 5433 |
| **Application** | MagoneAI API | FastAPI backend | 8080 |
| **Application** | MagoneAI Web | Next.js frontend | 3000 |
| **Workflow** | Temporal Server | Workflow orchestration | 7233 |
| **Workflow** | Temporal UI | Workflow monitoring | 8081 |
| **Workflow** | Temporal Workers | Task execution | - |
| **Database** | PostgreSQL | Primary data store | 5432 |
| **Cache** | Redis | Caching, sessions | 6379 |
| **Vector DB** | Qdrant | RAG embeddings | 6333, 6334 |
| **Monitoring** | Prometheus | Metrics collection | 9090 |
| **Monitoring** | Grafana | Dashboards | 3001 |
| **Monitoring** | Loki | Log aggregation | 3100 |
| **Monitoring** | AlertManager | Alert routing | 9093 |

---

## 3. Infrastructure Requirements

### Minimum Production Requirements

| Resource | Specification |
|----------|---------------|
| **CPU** | 8 cores |
| **RAM** | 32 GB |
| **Storage** | 200 GB SSD |
| **Network** | 1 Gbps |

### Recommended Production Requirements

| Resource | Specification |
|----------|---------------|
| **CPU** | 16+ cores |
| **RAM** | 64 GB |
| **Storage** | 500 GB NVMe SSD |
| **Network** | 10 Gbps |

### Cloud Instance Recommendations

| Provider | Instance Type | Monthly Cost (Est.) |
|----------|---------------|---------------------|
| **AWS** | m6i.2xlarge | ~$280 |
| **GCP** | n2-standard-8 | ~$260 |
| **Azure** | Standard_D8s_v5 | ~$275 |
| **DigitalOcean** | g-8vcpu-32gb | ~$240 |

---

## 4. Docker Compose Configuration

### 4.1 Main Docker Compose File

Create file: `deploy/docker-compose.production.yml`

```yaml
version: "3.9"

# ============================================================================
# MAGONEAI PRODUCTION DEPLOYMENT
# External API Access + Monitoring Stack
# ============================================================================

services:
  # ==========================================================================
  # EDGE LAYER - Traefik Reverse Proxy
  # ==========================================================================
  traefik:
    image: traefik:v3.2
    container_name: magoneai-traefik
    restart: always
    command:
      # API and Dashboard
      - "--api.dashboard=true"
      - "--api.insecure=false"
      # Providers
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.docker.network=magoneai-public"
      # Entrypoints
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      # HTTP to HTTPS redirect
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      # Let's Encrypt
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      # Metrics for Prometheus
      - "--metrics.prometheus=true"
      - "--metrics.prometheus.buckets=0.1,0.3,1.2,5.0"
      - "--metrics.prometheus.entryPoint=metrics"
      - "--entrypoints.metrics.address=:8082"
      # Access logs
      - "--accesslog=true"
      - "--accesslog.filepath=/var/log/traefik/access.log"
      - "--accesslog.format=json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_letsencrypt:/letsencrypt
      - traefik_logs:/var/log/traefik
    networks:
      - magoneai-public
      - magoneai-internal
    labels:
      # Dashboard
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.${DOMAIN}`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.entrypoints=websecure"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
      - "traefik.http.routers.dashboard.middlewares=dashboard-auth"
      - "traefik.http.middlewares.dashboard-auth.basicauth.users=${TRAEFIK_DASHBOARD_AUTH}"

  # ==========================================================================
  # API GATEWAY LAYER - Kong
  # ==========================================================================
  kong-database:
    image: postgres:16-alpine
    container_name: magoneai-kong-db
    restart: always
    environment:
      POSTGRES_USER: kong
      POSTGRES_PASSWORD: ${KONG_DB_PASSWORD}
      POSTGRES_DB: kong
    volumes:
      - kong_db_data:/var/lib/postgresql/data
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kong"]
      interval: 10s
      timeout: 5s
      retries: 5

  kong-migrations:
    image: kong:3.5-alpine
    container_name: magoneai-kong-migrations
    command: kong migrations bootstrap
    depends_on:
      kong-database:
        condition: service_healthy
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PG_USER: kong
      KONG_PG_PASSWORD: ${KONG_DB_PASSWORD}
    networks:
      - magoneai-internal
    restart: on-failure

  kong:
    image: kong:3.5-alpine
    container_name: magoneai-kong
    restart: always
    depends_on:
      kong-database:
        condition: service_healthy
      kong-migrations:
        condition: service_completed_successfully
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PG_USER: kong
      KONG_PG_PASSWORD: ${KONG_DB_PASSWORD}
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: "0.0.0.0:8001"
      KONG_PROXY_LISTEN: "0.0.0.0:8000"
      KONG_STATUS_LISTEN: "0.0.0.0:8100"
      # Prometheus plugin
      KONG_PLUGINS: bundled,prometheus
    ports:
      - "8001:8001"  # Admin API (internal only in production)
    networks:
      - magoneai-public
      - magoneai-internal
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 10s
      timeout: 5s
      retries: 5
    labels:
      - "traefik.enable=true"
      # API Gateway routes
      - "traefik.http.routers.kong.rule=Host(`api.${DOMAIN}`)"
      - "traefik.http.routers.kong.entrypoints=websecure"
      - "traefik.http.routers.kong.tls.certresolver=letsencrypt"
      - "traefik.http.routers.kong.service=kong"
      - "traefik.http.services.kong.loadbalancer.server.port=8000"

  # Konga - Kong Admin UI (optional, for easier management)
  konga:
    image: pantsel/konga:latest
    container_name: magoneai-konga
    restart: always
    depends_on:
      - kong
    environment:
      NODE_ENV: production
      TOKEN_SECRET: ${KONGA_TOKEN_SECRET}
      DB_ADAPTER: postgres
      DB_HOST: kong-database
      DB_USER: kong
      DB_PASSWORD: ${KONG_DB_PASSWORD}
      DB_DATABASE: konga
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.konga.rule=Host(`kong-admin.${DOMAIN}`)"
      - "traefik.http.routers.konga.entrypoints=websecure"
      - "traefik.http.routers.konga.tls.certresolver=letsencrypt"
      - "traefik.http.services.konga.loadbalancer.server.port=1337"

  # ==========================================================================
  # APPLICATION LAYER
  # ==========================================================================
  api:
    image: ${DOCKER_REGISTRY}/magoneai-api:${IMAGE_TAG:-latest}
    container_name: magoneai-api
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      temporal:
        condition: service_started
    environment:
      # Database
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      DATABASE_POOL_SIZE: 20
      DATABASE_MAX_OVERFLOW: 40
      # Temporal
      TEMPORAL_HOST: temporal:7233
      TEMPORAL_NAMESPACE: default
      TEMPORAL_TASK_QUEUE: agent-tasks
      WORKFLOW_TIMEOUT_SECONDS: 600
      # Redis
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      # Qdrant
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
      # LLM Providers
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      # Security
      SECRET_KEY: ${SECRET_KEY}
      SECRETS_ENCRYPTION_KEY: ${SECRETS_ENCRYPTION_KEY}
      # CORS (Kong handles external CORS)
      CORS_ORIGINS: "http://web:3000,https://${DOMAIN}"
      # Rate limiting (Kong handles external rate limiting)
      RATE_LIMITING_ENABLED: "false"
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "2"
          memory: 4G
        reservations:
          cpus: "0.5"
          memory: 1G

  worker:
    image: ${DOCKER_REGISTRY}/magoneai-worker:${IMAGE_TAG:-latest}
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      temporal:
        condition: service_started
    environment:
      # Database
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      # Temporal
      TEMPORAL_HOST: temporal:7233
      TEMPORAL_NAMESPACE: default
      TEMPORAL_TASK_QUEUE: agent-tasks
      # Qdrant
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
      # LLM Providers
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      # Security
      SECRETS_ENCRYPTION_KEY: ${SECRETS_ENCRYPTION_KEY}
    networks:
      - magoneai-internal
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "2"
          memory: 4G
        reservations:
          cpus: "0.25"
          memory: 512M

  web:
    image: ${DOCKER_REGISTRY}/magoneai-web:${IMAGE_TAG:-latest}
    container_name: magoneai-web
    restart: always
    depends_on:
      - api
    environment:
      NEXT_PUBLIC_API_URL: https://api.${DOMAIN}
      NODE_ENV: production
    networks:
      - magoneai-public
      - magoneai-internal
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`${DOMAIN}`) || Host(`www.${DOMAIN}`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.services.web.loadbalancer.server.port=3000"

  # ==========================================================================
  # WORKFLOW ENGINE - Temporal
  # ==========================================================================
  temporal:
    image: temporalio/auto-setup:1.22
    container_name: magoneai-temporal
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PWD=${DB_PASSWORD}
      - POSTGRES_SEEDS=postgres
      - PROMETHEUS_ENDPOINT=0.0.0.0:9090
    networks:
      - magoneai-internal
    ports:
      - "7233:7233"  # gRPC (internal)

  temporal-ui:
    image: temporalio/ui:2.22.3
    container_name: magoneai-temporal-ui
    restart: always
    depends_on:
      - temporal
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - TEMPORAL_CORS_ORIGINS=https://temporal.${DOMAIN}
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.temporal.rule=Host(`temporal.${DOMAIN}`)"
      - "traefik.http.routers.temporal.entrypoints=websecure"
      - "traefik.http.routers.temporal.tls.certresolver=letsencrypt"
      - "traefik.http.routers.temporal.middlewares=temporal-auth"
      - "traefik.http.middlewares.temporal-auth.basicauth.users=${TEMPORAL_UI_AUTH}"
      - "traefik.http.services.temporal.loadbalancer.server.port=8080"

  # ==========================================================================
  # DATA LAYER
  # ==========================================================================
  postgres:
    image: postgres:16-alpine
    container_name: magoneai-postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
      # Performance tuning
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"
      - "-c"
      - "effective_cache_size=1GB"
      - "-c"
      - "maintenance_work_mem=128MB"
      - "-c"
      - "checkpoint_completion_target=0.9"
      - "-c"
      - "wal_buffers=16MB"
      - "-c"
      - "default_statistics_target=100"
      - "-c"
      - "random_page_cost=1.1"
      - "-c"
      - "effective_io_concurrency=200"
      - "-c"
      - "log_statement=mod"
      - "-c"
      - "log_min_duration_statement=1000"

  redis:
    image: redis:7-alpine
    container_name: magoneai-redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --maxmemory 512mb --maxmemory-policy volatile-lru
    volumes:
      - redis_data:/data
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: magoneai-qdrant
    restart: always
    volumes:
      - qdrant_storage:/qdrant/storage
      - qdrant_snapshots:/qdrant/snapshots
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
      QDRANT__SERVICE__HTTP_PORT: 6333
      QDRANT__LOG_LEVEL: INFO
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/readiness"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==========================================================================
  # MONITORING LAYER
  # ==========================================================================
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: magoneai-prometheus
    restart: always
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=30d"
      - "--web.enable-lifecycle"
      - "--web.enable-admin-api"
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prometheus.rule=Host(`prometheus.${DOMAIN}`)"
      - "traefik.http.routers.prometheus.entrypoints=websecure"
      - "traefik.http.routers.prometheus.tls.certresolver=letsencrypt"
      - "traefik.http.routers.prometheus.middlewares=prometheus-auth"
      - "traefik.http.middlewares.prometheus-auth.basicauth.users=${MONITORING_AUTH}"
      - "traefik.http.services.prometheus.loadbalancer.server.port=9090"

  grafana:
    image: grafana/grafana:10.2.2
    container_name: magoneai-grafana
    restart: always
    depends_on:
      - prometheus
      - loki
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_SERVER_ROOT_URL: https://grafana.${DOMAIN}
      GF_INSTALL_PLUGINS: grafana-clock-panel,grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.${DOMAIN}`)"
      - "traefik.http.routers.grafana.entrypoints=websecure"
      - "traefik.http.routers.grafana.tls.certresolver=letsencrypt"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"

  loki:
    image: grafana/loki:2.9.2
    container_name: magoneai-loki
    restart: always
    volumes:
      - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - magoneai-internal

  promtail:
    image: grafana/promtail:2.9.2
    container_name: magoneai-promtail
    restart: always
    volumes:
      - ./monitoring/promtail/promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/log:/var/log:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_logs:/var/log/traefik:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - magoneai-internal
    depends_on:
      - loki

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: magoneai-alertmanager
    restart: always
    volumes:
      - ./monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    command:
      - "--config.file=/etc/alertmanager/alertmanager.yml"
      - "--storage.path=/alertmanager"
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.alertmanager.rule=Host(`alerts.${DOMAIN}`)"
      - "traefik.http.routers.alertmanager.entrypoints=websecure"
      - "traefik.http.routers.alertmanager.tls.certresolver=letsencrypt"
      - "traefik.http.routers.alertmanager.middlewares=alertmanager-auth"
      - "traefik.http.middlewares.alertmanager-auth.basicauth.users=${MONITORING_AUTH}"
      - "traefik.http.services.alertmanager.loadbalancer.server.port=9093"

  # Node exporter for host metrics
  node-exporter:
    image: prom/node-exporter:v1.7.0
    container_name: magoneai-node-exporter
    restart: always
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--path.rootfs=/rootfs"
      - "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"
    networks:
      - magoneai-internal

  # PostgreSQL exporter
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15.0
    container_name: magoneai-postgres-exporter
    restart: always
    environment:
      DATA_SOURCE_NAME: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}?sslmode=disable
    networks:
      - magoneai-internal
    depends_on:
      postgres:
        condition: service_healthy

  # Redis exporter
  redis-exporter:
    image: oliver006/redis_exporter:v1.55.0
    container_name: magoneai-redis-exporter
    restart: always
    environment:
      REDIS_ADDR: redis://redis:6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    networks:
      - magoneai-internal
    depends_on:
      redis:
        condition: service_healthy

# ==========================================================================
# NETWORKS
# ==========================================================================
networks:
  magoneai-public:
    driver: bridge
    name: magoneai-public
  magoneai-internal:
    driver: bridge
    name: magoneai-internal
    internal: true

# ==========================================================================
# VOLUMES
# ==========================================================================
volumes:
  traefik_letsencrypt:
  traefik_logs:
  kong_db_data:
  postgres_data:
  redis_data:
  qdrant_storage:
  qdrant_snapshots:
  prometheus_data:
  grafana_data:
  loki_data:
  alertmanager_data:
```

### 4.2 Environment Variables File

Create file: `deploy/.env.production.example`

```bash
# =============================================================================
# MAGONEAI PRODUCTION ENVIRONMENT CONFIGURATION
# =============================================================================

# -----------------------------------------------------------------------------
# DOMAIN CONFIGURATION
# -----------------------------------------------------------------------------
DOMAIN=magoneai.example.com
ACME_EMAIL=admin@example.com

# -----------------------------------------------------------------------------
# DOCKER REGISTRY
# -----------------------------------------------------------------------------
DOCKER_REGISTRY=your-registry.com
IMAGE_TAG=latest

# -----------------------------------------------------------------------------
# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------
DB_USER=magoneai
DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD_HERE
DB_NAME=magoneai

# -----------------------------------------------------------------------------
# KONG API GATEWAY
# -----------------------------------------------------------------------------
KONG_DB_PASSWORD=CHANGE_ME_KONG_DB_PASSWORD
KONGA_TOKEN_SECRET=CHANGE_ME_RANDOM_32_CHAR_STRING

# -----------------------------------------------------------------------------
# REDIS CONFIGURATION
# -----------------------------------------------------------------------------
REDIS_PASSWORD=CHANGE_ME_REDIS_PASSWORD

# -----------------------------------------------------------------------------
# APPLICATION SECRETS
# -----------------------------------------------------------------------------
# Generate with: openssl rand -hex 32
SECRET_KEY=CHANGE_ME_64_CHAR_HEX_STRING

# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
SECRETS_ENCRYPTION_KEY=CHANGE_ME_FERNET_KEY

# -----------------------------------------------------------------------------
# LLM API KEYS
# -----------------------------------------------------------------------------
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# -----------------------------------------------------------------------------
# AUTHENTICATION (htpasswd format)
# Generate with: htpasswd -nb admin password | sed 's/\$/\$\$/g'
# -----------------------------------------------------------------------------
TRAEFIK_DASHBOARD_AUTH=admin:$$apr1$$xyz$$hashedpassword
TEMPORAL_UI_AUTH=admin:$$apr1$$xyz$$hashedpassword
MONITORING_AUTH=admin:$$apr1$$xyz$$hashedpassword

# -----------------------------------------------------------------------------
# GRAFANA
# -----------------------------------------------------------------------------
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_GRAFANA_PASSWORD
```

---

## 5. API Gateway Configuration

### 5.1 Kong Configuration Script

Create file: `deploy/kong/configure-kong.sh`

```bash
#!/bin/bash
# =============================================================================
# Kong API Gateway Configuration Script
# =============================================================================

KONG_ADMIN_URL="http://localhost:8001"

echo "Waiting for Kong to be ready..."
until curl -s "$KONG_ADMIN_URL/status" > /dev/null 2>&1; do
    sleep 2
done
echo "Kong is ready!"

# -----------------------------------------------------------------------------
# Create MagoneAI API Service
# -----------------------------------------------------------------------------
echo "Creating MagoneAI API service..."
curl -s -X POST "$KONG_ADMIN_URL/services" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "magoneai-api",
    "url": "http://api:8000",
    "connect_timeout": 60000,
    "write_timeout": 60000,
    "read_timeout": 60000,
    "retries": 3
  }'

# -----------------------------------------------------------------------------
# Create Routes
# -----------------------------------------------------------------------------
echo "Creating API routes..."

# Main API route
curl -s -X POST "$KONG_ADMIN_URL/services/magoneai-api/routes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api-v1",
    "paths": ["/api/v1"],
    "strip_path": false,
    "preserve_host": true
  }'

# Health check route (no auth)
curl -s -X POST "$KONG_ADMIN_URL/services/magoneai-api/routes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "health",
    "paths": ["/health"],
    "strip_path": false
  }'

# -----------------------------------------------------------------------------
# Enable Plugins
# -----------------------------------------------------------------------------

# 1. Rate Limiting (Global)
echo "Enabling rate limiting..."
curl -s -X POST "$KONG_ADMIN_URL/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rate-limiting",
    "config": {
      "minute": 100,
      "hour": 1000,
      "policy": "local",
      "fault_tolerant": true,
      "hide_client_headers": false
    }
  }'

# 2. Rate Limiting for Workflow Execution (Stricter)
curl -s -X POST "$KONG_ADMIN_URL/routes/api-v1/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rate-limiting",
    "config": {
      "minute": 20,
      "hour": 200,
      "policy": "local"
    }
  }'

# 3. API Key Authentication
echo "Enabling API key authentication..."
curl -s -X POST "$KONG_ADMIN_URL/routes/api-v1/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "key-auth",
    "config": {
      "key_names": ["X-API-Key", "apikey"],
      "key_in_body": false,
      "key_in_header": true,
      "key_in_query": true,
      "hide_credentials": true
    }
  }'

# 4. CORS
echo "Enabling CORS..."
curl -s -X POST "$KONG_ADMIN_URL/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cors",
    "config": {
      "origins": ["*"],
      "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
      "headers": ["Accept", "Accept-Version", "Content-Length", "Content-MD5", "Content-Type", "Date", "X-Auth-Token", "X-API-Key", "Authorization"],
      "exposed_headers": ["X-Auth-Token", "X-RateLimit-Limit-Minute", "X-RateLimit-Remaining-Minute"],
      "credentials": true,
      "max_age": 3600
    }
  }'

# 5. Request Transformer (Add headers)
echo "Enabling request transformer..."
curl -s -X POST "$KONG_ADMIN_URL/routes/api-v1/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "request-transformer",
    "config": {
      "add": {
        "headers": ["X-Request-Source:kong-gateway"]
      }
    }
  }'

# 6. Response Transformer (Security headers)
echo "Enabling response transformer..."
curl -s -X POST "$KONG_ADMIN_URL/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "response-transformer",
    "config": {
      "add": {
        "headers": [
          "X-Content-Type-Options:nosniff",
          "X-Frame-Options:DENY",
          "X-XSS-Protection:1; mode=block"
        ]
      }
    }
  }'

# 7. Prometheus Metrics
echo "Enabling Prometheus metrics..."
curl -s -X POST "$KONG_ADMIN_URL/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prometheus",
    "config": {
      "status_code_metrics": true,
      "latency_metrics": true,
      "bandwidth_metrics": true,
      "upstream_health_metrics": true
    }
  }'

# 8. Request Size Limiting
echo "Enabling request size limiting..."
curl -s -X POST "$KONG_ADMIN_URL/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "request-size-limiting",
    "config": {
      "allowed_payload_size": 10,
      "size_unit": "megabytes"
    }
  }'

# 9. IP Restriction (Optional - for admin routes)
echo "Enabling IP restriction for admin..."
curl -s -X POST "$KONG_ADMIN_URL/routes/health/plugins" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ip-restriction",
    "config": {
      "allow": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    }
  }'

# -----------------------------------------------------------------------------
# Create API Consumers
# -----------------------------------------------------------------------------
echo "Creating API consumers..."

# Default consumer for internal use
curl -s -X POST "$KONG_ADMIN_URL/consumers" \
  -H "Content-Type: application/json" \
  -d '{"username": "internal-service"}'

curl -s -X POST "$KONG_ADMIN_URL/consumers/internal-service/key-auth" \
  -H "Content-Type: application/json" \
  -d '{"key": "internal-api-key-change-me"}'

# Example external consumer
curl -s -X POST "$KONG_ADMIN_URL/consumers" \
  -H "Content-Type: application/json" \
  -d '{"username": "external-client-1"}'

curl -s -X POST "$KONG_ADMIN_URL/consumers/external-client-1/key-auth" \
  -H "Content-Type: application/json" \
  -d '{"key": "ext-client-1-api-key-change-me"}'

echo ""
echo "Kong configuration complete!"
echo "API Gateway is ready at: https://api.your-domain.com"
```

### 5.2 Kong Consumer Management API

Create file: `deploy/kong/manage-consumers.sh`

```bash
#!/bin/bash
# =============================================================================
# Kong Consumer Management
# Usage: ./manage-consumers.sh [create|delete|list|rotate-key] [consumer-name]
# =============================================================================

KONG_ADMIN_URL="http://localhost:8001"
ACTION=$1
CONSUMER=$2

case $ACTION in
  create)
    if [ -z "$CONSUMER" ]; then
      echo "Usage: ./manage-consumers.sh create <consumer-name>"
      exit 1
    fi

    # Create consumer
    curl -s -X POST "$KONG_ADMIN_URL/consumers" \
      -H "Content-Type: application/json" \
      -d "{\"username\": \"$CONSUMER\"}"

    # Generate API key
    API_KEY=$(openssl rand -hex 32)
    curl -s -X POST "$KONG_ADMIN_URL/consumers/$CONSUMER/key-auth" \
      -H "Content-Type: application/json" \
      -d "{\"key\": \"$API_KEY\"}"

    echo "Consumer created: $CONSUMER"
    echo "API Key: $API_KEY"
    ;;

  delete)
    if [ -z "$CONSUMER" ]; then
      echo "Usage: ./manage-consumers.sh delete <consumer-name>"
      exit 1
    fi
    curl -s -X DELETE "$KONG_ADMIN_URL/consumers/$CONSUMER"
    echo "Consumer deleted: $CONSUMER"
    ;;

  list)
    echo "Consumers:"
    curl -s "$KONG_ADMIN_URL/consumers" | jq '.data[] | {username, created_at}'
    ;;

  rotate-key)
    if [ -z "$CONSUMER" ]; then
      echo "Usage: ./manage-consumers.sh rotate-key <consumer-name>"
      exit 1
    fi

    # Delete old keys
    OLD_KEYS=$(curl -s "$KONG_ADMIN_URL/consumers/$CONSUMER/key-auth" | jq -r '.data[].id')
    for KEY_ID in $OLD_KEYS; do
      curl -s -X DELETE "$KONG_ADMIN_URL/consumers/$CONSUMER/key-auth/$KEY_ID"
    done

    # Create new key
    NEW_KEY=$(openssl rand -hex 32)
    curl -s -X POST "$KONG_ADMIN_URL/consumers/$CONSUMER/key-auth" \
      -H "Content-Type: application/json" \
      -d "{\"key\": \"$NEW_KEY\"}"

    echo "New API Key for $CONSUMER: $NEW_KEY"
    ;;

  *)
    echo "Usage: ./manage-consumers.sh [create|delete|list|rotate-key] [consumer-name]"
    exit 1
    ;;
esac
```

---

## 6. Monitoring Setup

### 6.1 Prometheus Configuration

Create file: `deploy/monitoring/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: magoneai-production

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  # Prometheus self-monitoring
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # Traefik metrics
  - job_name: "traefik"
    static_configs:
      - targets: ["traefik:8082"]

  # Kong metrics
  - job_name: "kong"
    static_configs:
      - targets: ["kong:8100"]

  # MagoneAI API (via internal endpoint)
  - job_name: "magoneai-api"
    metrics_path: /metrics
    static_configs:
      - targets: ["api:8000"]

  # Temporal Server
  - job_name: "temporal"
    static_configs:
      - targets: ["temporal:9090"]

  # Node exporter (host metrics)
  - job_name: "node"
    static_configs:
      - targets: ["node-exporter:9100"]

  # PostgreSQL exporter
  - job_name: "postgres"
    static_configs:
      - targets: ["postgres-exporter:9187"]

  # Redis exporter
  - job_name: "redis"
    static_configs:
      - targets: ["redis-exporter:9121"]

  # Qdrant metrics
  - job_name: "qdrant"
    static_configs:
      - targets: ["qdrant:6333"]
    metrics_path: /metrics

  # Loki (log aggregator)
  - job_name: "loki"
    static_configs:
      - targets: ["loki:3100"]
```

### 6.2 Prometheus Alert Rules

Create file: `deploy/monitoring/prometheus/alerts.yml`

```yaml
groups:
  # ==========================================================================
  # Infrastructure Alerts
  # ==========================================================================
  - name: infrastructure
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for more than 5 minutes on {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 85% for more than 5 minutes"

      - alert: DiskSpaceRunningLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space running low"
          description: "Less than 20% disk space available"

      - alert: DiskSpaceCritical
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Disk space critical"
          description: "Less than 10% disk space available"

  # ==========================================================================
  # Application Alerts
  # ==========================================================================
  - name: magoneai-application
    rules:
      - alert: APIHighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate"
          description: "More than 5% of requests are failing"

      - alert: APIHighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is above 2 seconds"

      - alert: APIServiceDown
        expr: up{job="magoneai-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MagoneAI API is down"
          description: "The MagoneAI API service is not responding"

      - alert: WorkerDown
        expr: temporal_workflow_task_queue_age_seconds > 300
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Temporal worker backlog growing"
          description: "Tasks are waiting more than 5 minutes in queue"

  # ==========================================================================
  # Database Alerts
  # ==========================================================================
  - name: database
    rules:
      - alert: PostgresDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL database is not responding"

      - alert: PostgresHighConnections
        expr: sum(pg_stat_activity_count) > 180
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High PostgreSQL connections"
          description: "PostgreSQL has more than 180 active connections (max 200)"

      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis cache is not responding"

      - alert: RedisHighMemory
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis high memory usage"
          description: "Redis is using more than 90% of max memory"

      - alert: QdrantDown
        expr: up{job="qdrant"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Qdrant is down"
          description: "Qdrant vector database is not responding"

  # ==========================================================================
  # Kong API Gateway Alerts
  # ==========================================================================
  - name: kong-gateway
    rules:
      - alert: KongHighLatency
        expr: histogram_quantile(0.95, rate(kong_latency_bucket{type="request"}[5m])) > 3000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Kong high request latency"
          description: "95th percentile request latency is above 3 seconds"

      - alert: KongHighErrorRate
        expr: sum(rate(kong_http_requests_total{code=~"5.."}[5m])) / sum(rate(kong_http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Kong high error rate"
          description: "More than 5% of requests through Kong are failing"

      - alert: KongRateLimitHit
        expr: increase(kong_rate_limiting_total{status="rate-limited"}[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate limit hits"
          description: "More than 100 requests rate-limited in 5 minutes"

  # ==========================================================================
  # Workflow Engine Alerts
  # ==========================================================================
  - name: temporal-workflow
    rules:
      - alert: TemporalDown
        expr: up{job="temporal"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Temporal server is down"
          description: "Temporal workflow engine is not responding"

      - alert: WorkflowHighFailureRate
        expr: sum(rate(temporal_workflow_completed{status="failed"}[5m])) / sum(rate(temporal_workflow_completed[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High workflow failure rate"
          description: "More than 10% of workflows are failing"

      - alert: WorkflowQueueBacklog
        expr: temporal_workflow_task_queue_length > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Workflow task queue backlog"
          description: "More than 100 tasks waiting in queue"
```

### 6.3 AlertManager Configuration

Create file: `deploy/monitoring/alertmanager/alertmanager.yml`

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@magoneai.com'
  smtp_auth_username: 'alerts@magoneai.com'
  smtp_auth_password: 'your-app-password'

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: 'critical'
      group_wait: 10s
      repeat_interval: 1h

    - match:
        severity: warning
      receiver: 'warning'
      repeat_interval: 4h

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@magoneai.com'
        send_resolved: true

  - name: 'critical'
    email_configs:
      - to: 'oncall@magoneai.com'
        send_resolved: true
    # Slack integration (optional)
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts-critical'
        send_resolved: true
        title: '{{ .Status | toUpper }}: {{ .CommonAnnotations.summary }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'warning'
    email_configs:
      - to: 'team@magoneai.com'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
```

### 6.4 Loki Configuration

Create file: `deploy/monitoring/loki/loki-config.yml`

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://alertmanager:9093

limits_config:
  retention_period: 720h  # 30 days
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20
```

### 6.5 Promtail Configuration

Create file: `deploy/monitoring/promtail/promtail-config.yml`

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Docker container logs
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs:
      - json:
          expressions:
            tag:
          source: attrs
      - regex:
          expression: (?P<container_name>(?:[a-zA-Z0-9][a-zA-Z0-9_.-]+))\/.+
          source: tag
      - labels:
          stream:
          container_name:
      - output:
          source: output

  # Traefik access logs
  - job_name: traefik
    static_configs:
      - targets:
          - localhost
        labels:
          job: traefik
          __path__: /var/log/traefik/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            method: RequestMethod
            path: RequestPath
            status: DownstreamStatus
            duration: Duration
      - labels:
          level:
          method:
          status:
```

### 6.6 Grafana Provisioning

Create file: `deploy/monitoring/grafana/provisioning/datasources/datasources.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false

  - name: AlertManager
    type: alertmanager
    access: proxy
    url: http://alertmanager:9093
    editable: false
```

Create file: `deploy/monitoring/grafana/provisioning/dashboards/dashboards.yml`

```yaml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards
```

---

## 7. Deployment Steps

### 7.1 Pre-Deployment Checklist

```bash
# 1. Clone and navigate to project
cd /opt/magoneai

# 2. Create required directories
mkdir -p deploy/monitoring/{prometheus,grafana/provisioning/{datasources,dashboards},grafana/dashboards,loki,promtail,alertmanager}
mkdir -p deploy/kong
mkdir -p deploy/init-scripts

# 3. Copy configuration files (from this plan)
# ... copy all config files to their respective locations

# 4. Set permissions
chmod +x deploy/kong/*.sh

# 5. Create environment file
cp deploy/.env.production.example deploy/.env.production
# Edit with your actual values
nano deploy/.env.production

# 6. Generate secure passwords
echo "DB_PASSWORD=$(openssl rand -base64 32)" >> deploy/.env.production
echo "REDIS_PASSWORD=$(openssl rand -base64 32)" >> deploy/.env.production
echo "SECRET_KEY=$(openssl rand -hex 32)" >> deploy/.env.production
echo "KONG_DB_PASSWORD=$(openssl rand -base64 32)" >> deploy/.env.production
echo "KONGA_TOKEN_SECRET=$(openssl rand -base64 32)" >> deploy/.env.production

# 7. Generate auth strings
htpasswd -nb admin "$(openssl rand -base64 12)" | sed 's/\$/\$\$/g'
# Add output to TRAEFIK_DASHBOARD_AUTH, TEMPORAL_UI_AUTH, MONITORING_AUTH
```

### 7.2 Deployment Commands

```bash
# Navigate to deploy directory
cd /opt/magoneai/deploy

# Source environment
export $(cat .env.production | xargs)

# Pull latest images
docker-compose -f docker-compose.production.yml pull

# Start infrastructure first
docker-compose -f docker-compose.production.yml up -d postgres redis qdrant

# Wait for databases to be healthy
sleep 30

# Start Temporal
docker-compose -f docker-compose.production.yml up -d temporal temporal-ui

# Wait for Temporal
sleep 20

# Start Kong (API Gateway)
docker-compose -f docker-compose.production.yml up -d kong-database
sleep 10
docker-compose -f docker-compose.production.yml up -d kong-migrations kong konga

# Configure Kong
sleep 20
./kong/configure-kong.sh

# Start application services
docker-compose -f docker-compose.production.yml up -d api worker web

# Start monitoring stack
docker-compose -f docker-compose.production.yml up -d prometheus grafana loki promtail alertmanager node-exporter postgres-exporter redis-exporter

# Start Traefik (edge proxy)
docker-compose -f docker-compose.production.yml up -d traefik

# Verify all services
docker-compose -f docker-compose.production.yml ps
```

### 7.3 Post-Deployment Verification

```bash
# Check all services are running
docker-compose -f docker-compose.production.yml ps

# Check API health
curl -k https://api.${DOMAIN}/health

# Check Kong status
curl http://localhost:8001/status

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Test API with key
curl -H "X-API-Key: your-api-key" https://api.${DOMAIN}/api/v1/agents

# View logs
docker-compose -f docker-compose.production.yml logs -f api worker
```

---

## 8. Security Considerations

### 8.1 Network Security

| Port | Service | Access |
|------|---------|--------|
| 80, 443 | Traefik | Public |
| 8000 | Kong Proxy | Internal (via Traefik) |
| 8001 | Kong Admin | Internal only |
| 8080 | API | Internal only |
| 3000 | Web UI | Internal (via Traefik) |
| 5432 | PostgreSQL | Internal only |
| 6379 | Redis | Internal only |
| 6333 | Qdrant | Internal only |
| 7233 | Temporal | Internal only |
| 9090 | Prometheus | Internal (via Traefik with auth) |
| 3001 | Grafana | Internal (via Traefik) |

### 8.2 Security Checklist

- [ ] All passwords are unique and strong (32+ characters)
- [ ] TLS certificates are valid and auto-renewed
- [ ] API keys are rotated regularly (every 90 days)
- [ ] Database backups are encrypted
- [ ] Admin interfaces are protected with authentication
- [ ] Rate limiting is configured appropriately
- [ ] CORS is configured for allowed origins only
- [ ] Secrets are stored in environment variables, not in code
- [ ] Docker images are from trusted sources
- [ ] Host firewall allows only necessary ports

### 8.3 Backup Strategy

```bash
# PostgreSQL backup (daily)
docker exec magoneai-postgres pg_dump -U ${DB_USER} ${DB_NAME} | gzip > backups/postgres_$(date +%Y%m%d).sql.gz

# Qdrant backup (weekly)
curl -X POST "http://localhost:6333/collections/your_collection/snapshots"

# Redis backup (included via appendonly)
docker exec magoneai-redis redis-cli -a ${REDIS_PASSWORD} BGSAVE
```

---

## 9. Scaling Guidelines

### 9.1 Horizontal Scaling

```bash
# Scale API replicas
docker-compose -f docker-compose.production.yml up -d --scale api=3

# Scale workers based on queue depth
docker-compose -f docker-compose.production.yml up -d --scale worker=5

# Scale web UI
docker-compose -f docker-compose.production.yml up -d --scale web=2
```

### 9.2 Scaling Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU > 70% | 5 min | Add 1 API replica |
| Memory > 80% | 5 min | Add 1 worker |
| Queue depth > 50 | 2 min | Add 2 workers |
| Request latency > 2s | 5 min | Add 1 API replica |
| Error rate > 5% | 2 min | Investigate / rollback |

### 9.3 Resource Limits per Service

| Service | CPU Limit | Memory Limit | Replicas |
|---------|-----------|--------------|----------|
| API | 2 cores | 4 GB | 2-5 |
| Worker | 2 cores | 4 GB | 3-10 |
| Web | 1 core | 1 GB | 2 |
| PostgreSQL | 4 cores | 8 GB | 1 (primary) |
| Redis | 1 core | 1 GB | 1 |
| Qdrant | 2 cores | 4 GB | 1 |

---

## 10. Troubleshooting

### 10.1 Common Issues

**Kong returns 502 Bad Gateway**
```bash
# Check if API is healthy
docker logs magoneai-api
curl http://api:8000/health

# Check Kong upstream
curl http://localhost:8001/upstreams
```

**High API latency**
```bash
# Check database connections
docker exec magoneai-postgres psql -U ${DB_USER} -d ${DB_NAME} -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis memory
docker exec magoneai-redis redis-cli -a ${REDIS_PASSWORD} INFO memory

# Check worker queue
curl http://localhost:7233/api/v1/namespaces/default/task-queues/agent-tasks
```

**Workflows stuck**
```bash
# Check Temporal workers
docker logs magoneai-worker-1

# Check Temporal UI
# Visit https://temporal.${DOMAIN}

# Restart workers
docker-compose -f docker-compose.production.yml restart worker
```

**Certificate issues**
```bash
# Check Traefik logs
docker logs magoneai-traefik | grep -i acme

# Force certificate renewal
docker exec magoneai-traefik rm /letsencrypt/acme.json
docker restart magoneai-traefik
```

### 10.2 Health Check Endpoints

| Service | Endpoint | Expected |
|---------|----------|----------|
| API | `/health` | `{"status": "healthy"}` |
| Kong | `:8001/status` | `{"database": {"reachable": true}}` |
| Prometheus | `:9090/-/healthy` | `Prometheus is Healthy` |
| Grafana | `:3000/api/health` | `{"database": "ok"}` |
| Qdrant | `:6333/readiness` | `200 OK` |

### 10.3 Log Locations

```bash
# Application logs (via Docker)
docker-compose logs -f api worker web

# Access logs (Traefik)
docker exec magoneai-traefik cat /var/log/traefik/access.log

# Query logs in Grafana
# Use Loki datasource with query: {container_name="magoneai-api"}
```

---

## Appendix: Quick Reference

### URLs After Deployment

| Service | URL |
|---------|-----|
| Web UI | `https://magoneai.example.com` |
| API Gateway | `https://api.magoneai.example.com` |
| Temporal UI | `https://temporal.magoneai.example.com` |
| Grafana | `https://grafana.magoneai.example.com` |
| Prometheus | `https://prometheus.magoneai.example.com` |
| Kong Admin (Konga) | `https://kong-admin.magoneai.example.com` |
| Traefik Dashboard | `https://traefik.magoneai.example.com` |
| AlertManager | `https://alerts.magoneai.example.com` |

### API Usage Example

```bash
# Get API key from Kong admin
API_KEY="your-api-key"

# List agents
curl -H "X-API-Key: $API_KEY" \
  https://api.magoneai.example.com/api/v1/agents

# Execute workflow
curl -X POST -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  https://api.magoneai.example.com/api/v1/workflow/execute \
  -d '{
    "agent_id": "your-agent-id",
    "user_input": "Hello, how can you help me?",
    "session_id": "session-123"
  }'

# Create workflow definition
curl -X POST -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  https://api.magoneai.example.com/api/v1/workflow-definitions \
  -d '{
    "id": "my-workflow",
    "name": "My Custom Workflow",
    "steps": [...],
    "entry_step": "step-1"
  }'
```

---

*Document Version: 1.0*
*Last Updated: December 2024*
