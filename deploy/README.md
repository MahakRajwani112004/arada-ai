# MagOneAI Deployment Guide

This directory contains everything needed to deploy MagOneAI using Docker.

## Architecture

```
                                    ┌─────────────────┐
                                    │    Internet     │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │     Traefik     │
                                    │  (Port 80/443)  │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
           ┌────────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
           │   /api/*        │     │  /temporal/*    │     │      /*         │
           │                 │     │                 │     │                 │
           │   API Service   │     │  Temporal UI    │     │   Web Service   │
           │   (Port 8000)   │     │   (Port 8080)   │     │   (Port 3000)   │
           └────────┬────────┘     └─────────────────┘     └─────────────────┘
                    │
           ┌────────▼────────┐
           │  Worker Service │
           │   (Temporal)    │
           └────────┬────────┘
                    │
    ┌───────────────┼───────────────┬───────────────┐
    │               │               │               │
┌───▼───┐      ┌───▼───┐      ┌───▼───┐      ┌───▼───┐
│Postgres│     │ Redis │     │Qdrant │     │Temporal│
│  :5432 │     │ :6379 │     │ :6333 │     │ :7233  │
└────────┘     └───────┘     └───────┘     └────────┘
```

## Quick Start

### Option 1: One-Line Install

```bash
./install.sh --domain app.yourdomain.com --tag latest
```

### Option 2: Manual Setup

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Start services
docker-compose up -d

# 3. Check status
docker-compose ps
```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DOMAIN` | Your domain name | `app.magoneai.com` |
| `DB_PASSWORD` | PostgreSQL password | (auto-generated) |
| `SECRET_KEY` | Application secret | (auto-generated) |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IMAGE_TAG` | Docker image version | `latest` |
| `DOCKER_REGISTRY` | Docker registry | `magoneai` |
| `REDIS_PASSWORD` | Redis password | `redis_secret` |
| `ACME_EMAIL` | Let's Encrypt email | - |

## Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Production setup with Traefik |
| `docker-compose.local.yml` | Local development (no SSL) |
| `.env.example` | Environment template |
| `install.sh` | Automated installer |
| `init-db.sql` | Database initialization |

## URL Routing

All services are accessed through a single domain:

| Path | Service | Description |
|------|---------|-------------|
| `/` | Web | Next.js frontend |
| `/api/*` | API | FastAPI backend |
| `/api/docs` | API | Swagger documentation |
| `/temporal/*` | Temporal UI | Workflow monitoring |
| `/health` | API | Health check endpoint |

## Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Stop and remove volumes (DESTRUCTIVE)
docker-compose down -v

# Restart a service
docker-compose restart api

# Scale workers
docker-compose up -d --scale worker=3

# Pull latest images
docker-compose pull

# Update to new version
export IMAGE_TAG=v1.1.0
docker-compose pull
docker-compose up -d
```

## SSL/TLS Certificates

### Development (Self-Signed)

By default, Traefik uses self-signed certificates. Accept the browser warning.

### Production (Let's Encrypt)

1. Uncomment Let's Encrypt lines in `docker-compose.yml`
2. Set `ACME_EMAIL` in `.env`
3. Ensure your domain DNS points to your server
4. Restart Traefik: `docker-compose restart traefik`

## Monitoring

### Service Health

```bash
# Check all services
docker-compose ps

# Check API health
curl -k https://localhost/health

# Check Temporal
curl http://localhost:7233/health
```

### Logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f api worker

# Last 100 lines
docker-compose logs --tail=100 api
```

## Backup & Restore

### Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U magone magone_db > backup.sql

# Backup volumes
docker run --rm -v magone_postgres_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/postgres_data.tar.gz /data
```

### Restore

```bash
# Restore PostgreSQL
docker-compose exec -T postgres psql -U magone magone_db < backup.sql
```

## Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose logs api
docker-compose logs worker

# Check if ports are in use
netstat -tlnp | grep -E '80|443|8000|3000'
```

### Database connection errors

```bash
# Check PostgreSQL is healthy
docker-compose exec postgres pg_isready -U magone

# Check connection string
docker-compose exec api env | grep DATABASE_URL
```

### Temporal connection errors

```bash
# Check Temporal is running
docker-compose logs temporal

# Test connection
docker-compose exec worker python -c "
from temporalio.client import Client
import asyncio
asyncio.run(Client.connect('temporal:7233'))
print('Connected!')
"
```

## Scaling

### Horizontal Scaling

```bash
# Scale workers
docker-compose up -d --scale worker=5

# Scale API (with load balancer)
docker-compose up -d --scale api=3
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Set strong `SECRET_KEY`
- [ ] Enable SSL with Let's Encrypt
- [ ] Restrict Traefik dashboard access
- [ ] Configure firewall rules
- [ ] Enable Redis password
- [ ] Review network policies
