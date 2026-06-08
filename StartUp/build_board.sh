#!/bin/bash
# Сборка дистрибутива борта (wheels MavixBoard).
# Запускать на машине с архитектурой борта (обычно сама RPi / aarch64).
set -e
SERVER_IP="85.198.102.188"        # подставь свой IP/домен сервера
cd "$(dirname "$0")/../MavixServer"
./scripts/build_wheels.sh ../MavixBoard
echo
echo "==> Готово. Wheels борта: $(pwd)/wheels/board/"
echo "==> Перенести на сервер:"
echo "    scp -r wheels/board/* root@${SERVER_IP}:/srv/mavix/MavixServer/wheels/board/"
