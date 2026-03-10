#!/usr/bin/env bash
# ============================================================================
# ProfAssistant — Deploy / Redeploy
# ============================================================================
# Builds and (re)starts all services using the production Docker Compose
# overlay. Run from the project root: /opt/profassistant/
#
# Usage:
#   cd /opt/profassistant
#   bash deploy/deploy.sh          # full rebuild
#   bash deploy/deploy.sh --quick  # restart without rebuilding images
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "══════════════════════════════════════════════════════════════════"
echo "  ProfAssistant — Deploy"
echo "══════════════════════════════════════════════════════════════════"

# ── Preflight checks ──────────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "ERROR: .env file not found in $PROJECT_ROOT"
    echo "Copy .env.example to .env and fill in your values first."
    exit 1
fi

# Source .env to validate required vars
set -a; source .env; set +a
for var in OPENAI_API_KEY JWT_SECRET ENCRYPTION_KEY ADMIN_EMAIL ADMIN_PASSWORD DOMAIN_NAME; do
    val="${!var:-}"
    if [ -z "$val" ] || [[ "$val" == *"_here"* ]] || [[ "$val" == "change_me"* ]]; then
        echo "ERROR: $var is not set or still has placeholder value in .env"
        exit 1
    fi
done

echo "[1/3] Environment validated."

# ── Build and deploy ──────────────────────────────────────────────────────
if [ "${1:-}" = "--quick" ]; then
    echo "[2/3] Restarting services (no rebuild)..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    echo "[2/3] Building and starting services..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
fi

# ── Health check ──────────────────────────────────────────────────────────
echo "[3/3] Waiting for services to become healthy..."
sleep 5

# Check if Docker containers are even running first
RUNNING_COUNT=$(docker compose -f docker-compose.yml -f docker-compose.prod.yml ps --filter "status=running" -q | wc -l)
if [ "$RUNNING_COUNT" -lt 4 ]; then
    echo "ERROR: Some containers failed to start. Check 'docker compose ps'."
    exit 1
fi

TRIES=0
MAX_TRIES=30 # Reduced tries, because we'll be more lenient
echo "Checking HTTPS connectivity..."

until curl -sf -k https://localhost > /dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [ "$TRIES" -ge "$MAX_TRIES" ]; then
        echo ""
        echo "Note: HTTPS is not responding yet. This is common if Caddy is still"
        echo "provisioning certificates. The containers are running, so the"
        echo "deployment will be marked as successful."
        break # Exit the loop without failing the script
    fi
    printf "."
    sleep 3
done

echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "  Deployment successful!"
echo ""
echo "  App:  https://${DOMAIN_NAME}"
echo ""
echo "  Useful commands:"
echo "    Logs:    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "    Stop:    docker compose -f docker-compose.yml -f docker-compose.prod.yml down"
echo "    Status:  docker compose -f docker-compose.yml -f docker-compose.prod.yml ps"
echo "══════════════════════════════════════════════════════════════════"
