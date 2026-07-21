#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_FILE="${ROOT_DIR}/deploy/sql/local_seed.sql"

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3307}"
MYSQL_DB="${MYSQL_DB:-agent_eval}"
MYSQL_USER="${MYSQL_USER:-agent}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-agent123}"

cat <<EOF
Exporting local SQL seed snapshot...
  host: ${MYSQL_HOST}:${MYSQL_PORT}
  db:   ${MYSQL_DB}
  user: ${MYSQL_USER}
  out:  ${OUTPUT_FILE}
EOF

mysqldump \
  -h"${MYSQL_HOST}" \
  -P"${MYSQL_PORT}" \
  -u"${MYSQL_USER}" \
  -p"${MYSQL_PASSWORD}" \
  --single-transaction \
  --skip-triggers \
  --no-create-info \
  --skip-comments \
  "${MYSQL_DB}" \
  metric_definitions \
  evaluation_strategies > "${OUTPUT_FILE}"

echo "Done. Commit ${OUTPUT_FILE} together with schema/model changes."
