#!/bin/sh
set -eu

REGISTRY="${IMAGE_REGISTRY:-${CI_REGISTRY:-}}"
REGISTRY_USER="${IMAGE_REGISTRY_USER:-${CI_REGISTRY_USER:-}}"
REGISTRY_PASSWORD="${IMAGE_REGISTRY_PASSWORD:-${CI_REGISTRY_PASSWORD:-}}"

required_vars="DEPLOY_HOST DEPLOY_USER DEPLOY_PATH BACKEND_IMAGE FRONTEND_IMAGE"
for var in $required_vars; do
  eval "value=\${$var:-}"
  if [ -z "$value" ]; then
    echo "[deploy] missing required variable: $var"
    exit 1
  fi
done

if [ -z "$REGISTRY" ] || [ -z "$REGISTRY_USER" ] || [ -z "$REGISTRY_PASSWORD" ]; then
  echo "[deploy] missing registry credentials (IMAGE_* or CI_REGISTRY* variables)"
  exit 1
fi

DEPLOY_PORT="${DEPLOY_PORT:-22}"
DEPLOY_COMPOSE_FILE="${DEPLOY_COMPOSE_FILE:-docker-compose.yml}"

ssh_opts="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p $DEPLOY_PORT"

echo "[deploy] target=${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}"

echo "[deploy] render compose override"
ssh $ssh_opts "${DEPLOY_USER}@${DEPLOY_HOST}" \
  "cd '${DEPLOY_PATH}' && cat > .ci.override.yml <<'EOF'
services:
  backend:
    image: ${BACKEND_IMAGE}
  frontend:
    image: ${FRONTEND_IMAGE}
EOF"

echo "[deploy] docker login / pull / up"
ssh $ssh_opts "${DEPLOY_USER}@${DEPLOY_HOST}" \
  "cd '${DEPLOY_PATH}' && echo '${REGISTRY_PASSWORD}' | docker login -u '${REGISTRY_USER}' --password-stdin '${REGISTRY}' && docker compose -f '${DEPLOY_COMPOSE_FILE}' -f .ci.override.yml pull backend frontend && docker compose -f '${DEPLOY_COMPOSE_FILE}' -f .ci.override.yml up -d backend frontend"

echo "[deploy] done"
