#!/usr/bin/env bash
# Обновить и перезапустить серверную часть (MavixServer + MavixWeb + PostgreSQL)
# на VPS: git pull в каталоге деплоя и docker compose up -d --build.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
_require_server_ip

ssh "${SERVER_USER}@${SERVER_IP}" bash -s <<EOF
set -euo pipefail
cd "${SERVER_COMPOSE_DIR}"
git pull
docker compose up -d --build
docker compose ps
EOF
echo "Готово: сервер обновлён и перезапущен на ${SERVER_IP}."
