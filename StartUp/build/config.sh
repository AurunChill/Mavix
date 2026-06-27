#!/usr/bin/env bash
# Общие параметры сборки и отправки на сервер.
# ПОДСТАВЬТЕ свои значения (как минимум SERVER_IP).

SERVER_IP="85.198.69.77"                     # IP или домен VPS с MavixServer
SERVER_USER="root"                        # пользователь SSH
SERVER_PREBUILT="/srv/mavix/MavixServer/prebuilt"   # куда класть готовые бинари десктопа
SERVER_WHEELS="/srv/mavix/MavixServer/wheels/board" # куда класть wheels борта
SERVER_COMPOSE_DIR="/srv/mavix"           # каталог с docker-compose.yml на сервере

# Корень репозитория (этот файл лежит в StartUp/build/).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

_require_server_ip() {
    if [ "$SERVER_IP" = "CHANGE_ME" ]; then
        echo "ОШИБКА: задайте SERVER_IP в StartUp/build/config.sh" >&2
        exit 1
    fi
}
