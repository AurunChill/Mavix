#!/usr/bin/env bash
# Собрать Python-wheels борта (MavixBoard) и отправить на сервер.
# Сервер отдаёт их как tar.gz при скачивании дистрибутива борта; кэш
# инвалидируется по хешу wheels автоматически — перезапуск не нужен.
# Запускать на машине с архитектурой целевого борта (обычно сама RPi / aarch64).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
_require_server_ip

cd "$REPO_ROOT/MavixServer"
./scripts/build_wheels.sh ../MavixBoard
ls -lh wheels/board/

scp -r wheels/board/* "${SERVER_USER}@${SERVER_IP}:${SERVER_WHEELS}/"
echo "Готово: wheels борта отправлены в ${SERVER_WHEELS} на ${SERVER_IP}."
