#!/bin/bash
# MagOneAI Installation Script
# Usage: ./install.sh [--domain yourdomain.com] [--tag v1.0.0]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DOMAIN="localhost"
IMAGE_TAG="latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--domain yourdomain.com] [--tag v1.0.0]"
            echo ""
            echo "Options:"
            echo "  --domain    Domain for the application (default: localhost)"
            echo "  --tag       Docker image tag to use (default: latest)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                MagOneAI Installation Script                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check if .env exists
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"

    # Generate random passwords
    DB_PASSWORD=$(openssl rand -hex 16)
    SECRET_KEY=$(openssl rand -hex 32)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    SECRETS_ENCRYPTION_KEY=$(openssl rand -hex 32)

    # Update .env with generated values
    sed -i.bak "s/DB_PASSWORD=.*/DB_PASSWORD=${DB_PASSWORD}/" "${SCRIPT_DIR}/.env"
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" "${SCRIPT_DIR}/.env"
    sed -i.bak "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=${REDIS_PASSWORD}/" "${SCRIPT_DIR}/.env"
    sed -i.bak "s/SECRETS_ENCRYPTION_KEY=.*/SECRETS_ENCRYPTION_KEY=${SECRETS_ENCRYPTION_KEY}/" "${SCRIPT_DIR}/.env"
    sed -i.bak "s/DOMAIN=.*/DOMAIN=${DOMAIN}/" "${SCRIPT_DIR}/.env"
    sed -i.bak "s/IMAGE_TAG=.*/IMAGE_TAG=${IMAGE_TAG}/" "${SCRIPT_DIR}/.env"
    rm -f "${SCRIPT_DIR}/.env.bak"

    echo -e "${GREEN}✓ Generated secure passwords${NC}"
    echo -e "${YELLOW}⚠ Please edit ${SCRIPT_DIR}/.env to add your API keys${NC}"
fi

# Prompt for required API keys if not set
source "${SCRIPT_DIR}/.env"

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key" ]; then
    echo ""
    read -p "Enter your OpenAI API Key (or press Enter to skip): " OPENAI_KEY
    if [ -n "$OPENAI_KEY" ]; then
        sed -i.bak "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=${OPENAI_KEY}|" "${SCRIPT_DIR}/.env"
        rm -f "${SCRIPT_DIR}/.env.bak"
    fi
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "sk-ant-your-anthropic-api-key" ]; then
    echo ""
    read -p "Enter your Anthropic API Key (or press Enter to skip): " ANTHROPIC_KEY
    if [ -n "$ANTHROPIC_KEY" ]; then
        sed -i.bak "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=${ANTHROPIC_KEY}|" "${SCRIPT_DIR}/.env"
        rm -f "${SCRIPT_DIR}/.env.bak"
    fi
fi

# Pull images
echo ""
echo -e "${YELLOW}Pulling Docker images...${NC}"
cd "${SCRIPT_DIR}"
docker-compose pull

# Start services
echo ""
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check service status
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗"
echo "║                   Installation Complete!                    ║"
echo "╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Services are starting up. Check status with:"
echo "  docker-compose ps"
echo ""
echo "Access your application:"
if [ "$DOMAIN" = "localhost" ]; then
    echo "  - Web UI:      https://localhost (accept self-signed cert)"
    echo "  - API Docs:    https://localhost/api/docs"
    echo "  - Temporal UI: https://localhost/temporal"
else
    echo "  - Web UI:      https://${DOMAIN}"
    echo "  - API Docs:    https://${DOMAIN}/api/docs"
    echo "  - Temporal UI: https://${DOMAIN}/temporal"
fi
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
