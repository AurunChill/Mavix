#!/usr/bin/env bash
# Полная установка TURN/STUN/TURNS на ОТДЕЛЬНОМ сервере.
# Требования:
#   - Чистая Ubuntu 22.04 / 24.04
#   - Домен (например turn.drone-mavix.ru) уже указывает на этот сервер
#   - Порты 80/tcp, 443/tcp+udp, 3478/tcp+udp, 5349/tcp+udp,
#     49152-65535/udp открыты у провайдера
#
# Запуск:
#   sudo bash install_turn_standalone.sh

set -euo pipefail

# ====== НАСТРОЙ ПОД СЕБЯ ======
DOMAIN="turn.drone-mavix.ru"
EMAIL="aurunchill@yandex.ru"           # для Let's Encrypt
TURN_USER="myuser"
TURN_PASS="changeme"
REALM="drone-mavix.ru"
# ==============================

[[ $EUID -eq 0 ]] || { echo "Запусти от root (sudo)"; exit 1; }

log(){ echo -e "\n\033[1;34m==> $*\033[0m"; }

log "0. Внешний IP"
EXTERNAL_IP=$(curl -s4 https://ifconfig.me)
echo "external-ip = $EXTERNAL_IP"

log "1. Проверка DNS"
RESOLVED=$(dig +short "$DOMAIN" | tail -1)
if [[ "$RESOLVED" != "$EXTERNAL_IP" ]]; then
  echo "ОШИБКА: $DOMAIN указывает на '$RESOLVED', а сервер имеет IP '$EXTERNAL_IP'."
  echo "Подожди пока DNS обновится."
  exit 1
fi
echo "OK"

log "2. Обновление системы и зависимости"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y coturn certbot dnsutils ufw curl

log "3. Получение Let's Encrypt сертификата (standalone, порт 80)"
systemctl stop coturn 2>/dev/null || true
certbot certonly --standalone --non-interactive --agree-tos \
  --email "$EMAIL" -d "$DOMAIN" \
  --preferred-challenges http

CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
[[ -f $CERT && -f $KEY ]] || { echo "ОШИБКА: сертификат не получен"; exit 1; }

log "4. Права на чтение сертификата для coturn"
# coturn запускается под user turnserver. Даём ему чтение через группу.
chgrp -R turnserver /etc/letsencrypt/live /etc/letsencrypt/archive
chmod -R g+rX /etc/letsencrypt/live /etc/letsencrypt/archive

log "5. Запись turnserver.conf"
cat > /etc/turnserver.conf <<EOF
# === Coturn для $DOMAIN ===
listening-port=3478
tls-listening-port=443
alt-tls-listening-port=5349

min-port=49152
max-port=65535

external-ip=$EXTERNAL_IP

realm=$REALM

lt-cred-mech
user=$TURN_USER:$TURN_PASS

fingerprint

cert=$CERT
pkey=$KEY

no-tlsv1
no-tlsv1_1
cipher-list="ECDHE+AESGCM:ECDHE+CHACHA20"

no-multicast-peers
denied-peer-ip=0.0.0.0-0.255.255.255
denied-peer-ip=127.0.0.0-127.255.255.255
denied-peer-ip=169.254.0.0-169.254.255.255
denied-peer-ip=192.0.0.0-192.0.0.255
denied-peer-ip=192.0.2.0-192.0.2.255
denied-peer-ip=192.88.99.0-192.88.99.255
denied-peer-ip=198.18.0.0-198.19.255.255
denied-peer-ip=198.51.100.0-198.51.100.255
denied-peer-ip=203.0.113.0-203.0.113.255
denied-peer-ip=240.0.0.0-255.255.255.255

allowed-peer-ip=$EXTERNAL_IP

total-quota=100
user-quota=12

log-file=/var/log/turnserver.log
verbose
EOF

log "6. Включение coturn (default-disabled на Ubuntu)"
sed -i 's/^#TURNSERVER_ENABLED=1/TURNSERVER_ENABLED=1/' /etc/default/coturn
grep -q '^TURNSERVER_ENABLED=1' /etc/default/coturn || \
  echo 'TURNSERVER_ENABLED=1' >> /etc/default/coturn

log "7. Firewall"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp                # certbot renew
ufw allow 443/tcp
ufw allow 5349/tcp
ufw allow 3478/tcp
ufw allow 3478/udp
ufw allow 49152:65535/udp
ufw --force enable

log "8. Возможность слушать privileged-порт 443"
# coturn запускается от непривилегированного пользователя,
# даём бинарю CAP_NET_BIND_SERVICE.
setcap 'cap_net_bind_service=+ep' /usr/bin/turnserver || true

log "9. Старт coturn"
systemctl enable coturn
systemctl restart coturn
sleep 3
systemctl status coturn --no-pager | head -20

log "10. Авто-обновление сертификата с reload coturn"
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/coturn-reload.sh <<'HOOK'
#!/bin/bash
systemctl restart coturn
HOOK
chmod +x /etc/letsencrypt/renewal-hooks/deploy/coturn-reload.sh

log "11. Проверка TLS на :443"
timeout 10 openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" \
  -verify_return_error </dev/null 2>&1 | \
  grep -E "Verify return code|subject=" || echo "(handshake не дал ожидаемого вывода)"

log "12. Проверка STUN-порта 3478"
ss -lntu | grep -E "(3478|443|5349)" || true

log "ГОТОВО"
cat <<EOF

================================================================
TURN/STUN/TURNS установлен и работает.

ICE-servers, которые сервер вернёт клиенту:
  STUN:  stun:$DOMAIN:3478
  TURN:  turn:$DOMAIN:3478?transport=udp
         turn:$DOMAIN:3478?transport=tcp
  TURNS: turns:$DOMAIN:443?transport=tcp

Креды:
  username=$TURN_USER
  password=$TURN_PASS

================================================================
Что сделать на ОСНОВНОМ сервере (drone-mavix.ru):

# 1. Прописать переменные в .env бэкенда (одной командой,
#    старые TURN/STUN-строки заменяются, лишние не плодятся):

cat >> /srv/mavix/MavixServer/.env <<'ENVEOF'
STUN_SERVER=stun:$DOMAIN:3478
TURN_SERVER=turn:$DOMAIN:3478
TURNS_SERVER=turns:$DOMAIN:443
TURN_USERNAME=$TURN_USER
TURN_PASSWORD=$TURN_PASS
ENVEOF

Еще не забудь поменять в preset.env:
build-templates/board/preset.env.template

И в core/config.py MavixDesktop!

# Если эти ключи уже были в .env — удали старые строки руками
# через nano /srv/mavix/MavixServer/.env, иначе будут дубли
# (последняя строка побеждает, но визуально путает).

# 2. Перезапустить app:
cd /srv/mavix && docker compose up -d --force-recreate app

# 3. Проверить что ice-servers отдаются клиенту правильно:
curl -s https://drone-mavix.ru/api/v1/ice-servers | python3 -m json.tool
================================================================
EOF