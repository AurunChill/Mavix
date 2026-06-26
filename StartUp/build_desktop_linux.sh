#!/bin/bash
# Сборка Linux-бинаря MavixDesktop (PyInstaller).
# Билдить лучше на относительно старом Linux (Ubuntu 22.04/24.04) — бинарь
# зависит от glibc хоста сборки.
set -e
SERVER_IP="85.198.69.77"        # подставь свой IP/домен сервера
cd "$(dirname "$0")/../MavixDesktop-UI"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pyinstaller
./scripts/build_binary.sh
echo
echo "==> Готово. Бинарь: $(pwd)/dist/mavixdesktop-linux"
echo "==> Перенести на сервер:"
echo "    scp dist/mavixdesktop-linux root@${SERVER_IP}:/srv/mavix/MavixServer/prebuilt/"
