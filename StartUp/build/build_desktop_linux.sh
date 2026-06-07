#!/usr/bin/env bash
# Собрать Linux-бинарь MavixDesktop (PyInstaller) и отправить на сервер,
# затем перезапустить контейнер app (сайт начнёт отдавать его как .AppImage).
# Билдить лучше на относительно старом Linux (Ubuntu 22.04/24.04) — бинарь
# зависит от glibc хоста сборки.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
_require_server_ip

cd "$REPO_ROOT/MavixDesktop-UI"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -e .
pip install pyinstaller
./scripts/build_binary.sh         # результат: dist/mavixdesktop-linux (~150 МБ)

scp dist/mavixdesktop-linux "${SERVER_USER}@${SERVER_IP}:${SERVER_PREBUILT}/"
ssh "${SERVER_USER}@${SERVER_IP}" "cd ${SERVER_COMPOSE_DIR} && docker compose restart app"
echo "Готово: Linux-бинарь отправлен, контейнер app перезапущен."
echo "Если pip жалуется на dev-пакеты: sudo apt install libgl1 libegl1 libxkbcommon0"
