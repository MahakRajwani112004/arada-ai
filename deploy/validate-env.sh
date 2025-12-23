#!/bin/bash
# MagOneAI Environment Validation Script
# Run this before deploying to production to validate required environment variables

set -e

echo "==================================="
echo "MagOneAI Environment Validation"
echo "==================================="
echo ""

ERRORS=0
WARNINGS=0

# Function to check required variable
check_required() {
    local var_name=$1
    local var_value=${!var_name}
    local description=$2

    if [ -z "$var_value" ]; then
        echo "ERROR: $var_name is required - $description"
        ((ERRORS++))
    else
        echo "  OK: $var_name is set"
    fi
}

# Function to check optional variable with warning
check_optional() {
    local var_name=$1
    local var_value=${!var_name}
    local description=$2

    if [ -z "$var_value" ]; then
        echo "WARN: $var_name is not set - $description"
        ((WARNINGS++))
    else
        echo "  OK: $var_name is set"
    fi
}

# Function to validate secret strength
check_secret_strength() {
    local var_name=$1
    local var_value=${!var_name}
    local min_length=$2

    if [ -n "$var_value" ]; then
        local length=${#var_value}
        if [ $length -lt $min_length ]; then
            echo "ERROR: $var_name must be at least $min_length characters (currently $length)"
            ((ERRORS++))
        fi
    fi
}

echo "Checking required variables..."
echo "-----------------------------"

# Domain and Infrastructure
check_required "DOMAIN" "Domain for the application (e.g., app.example.com)"
check_required "DB_PASSWORD" "PostgreSQL database password"

# Security
check_required "SECRET_KEY" "Application secret key (generate with: openssl rand -hex 32)"
check_required "SECRETS_ENCRYPTION_KEY" "Fernet encryption key for secrets vault"
check_required "TRAEFIK_DASHBOARD_AUTH" "Traefik dashboard basic auth (generate with: htpasswd -nb admin yourpassword)"

# Check secret strength
check_secret_strength "SECRET_KEY" 32
check_secret_strength "DB_PASSWORD" 12

echo ""
echo "Checking LLM provider keys..."
echo "-----------------------------"

# At least one LLM provider is required
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: At least one LLM provider API key is required (OPENAI_API_KEY or ANTHROPIC_API_KEY)"
    ((ERRORS++))
else
    [ -n "$OPENAI_API_KEY" ] && echo "  OK: OPENAI_API_KEY is set"
    [ -n "$ANTHROPIC_API_KEY" ] && echo "  OK: ANTHROPIC_API_KEY is set"
fi

echo ""
echo "Checking optional variables..."
echo "-----------------------------"

check_optional "ACME_EMAIL" "Email for Let's Encrypt SSL certificates"
check_optional "REDIS_PASSWORD" "Redis password (will use default if not set)"
check_optional "CORS_ORIGINS" "Allowed CORS origins (will default to DOMAIN)"
check_optional "GOOGLE_CLIENT_ID" "Google OAuth client ID (required for Calendar/Gmail integration)"
check_optional "GOOGLE_CLIENT_SECRET" "Google OAuth client secret"

echo ""
echo "Checking security configuration..."
echo "-----------------------------"

# Check CORS origins don't contain wildcard
if [ -n "$CORS_ORIGINS" ] && [[ "$CORS_ORIGINS" == *"*"* ]]; then
    echo "ERROR: CORS_ORIGINS cannot contain '*' in production"
    ((ERRORS++))
else
    echo "  OK: CORS_ORIGINS does not contain wildcard"
fi

# Check Traefik auth is not default
if [ -n "$TRAEFIK_DASHBOARD_AUTH" ]; then
    if [[ "$TRAEFIK_DASHBOARD_AUTH" == "admin:"* ]] && [[ "$TRAEFIK_DASHBOARD_AUTH" != *"$apr1$"* ]]; then
        echo "WARN: TRAEFIK_DASHBOARD_AUTH appears to be using a simple password"
        ((WARNINGS++))
    else
        echo "  OK: TRAEFIK_DASHBOARD_AUTH appears to be properly hashed"
    fi
fi

echo ""
echo "==================================="
echo "Validation Summary"
echo "==================================="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "FAILED: Please fix the errors above before deploying"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "PASSED with warnings: Review the warnings above"
    exit 0
else
    echo "PASSED: All required variables are set correctly"
    exit 0
fi
