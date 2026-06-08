# Развёртывание Mavix на сервере (ForServer/Main)

Серверная часть Mavix (MavixServer + MavixWeb + PostgreSQL + TLS-прокси Caddy)
поднимается одним `docker compose` из этого каталога. Здесь лежат общие файлы
оркестрации; репозитории компонентов клонируются рядом.

## Состав каталога
- `docker-compose.yaml` — сервисы: `db` (PostgreSQL 16), `migrator` (миграции
  Alembic), `app` (MavixServer), `web` (MavixWeb), `caddy` (TLS reverse-proxy).
- `Caddyfile` — TLS и маршрутизация: `/api/*`, `/ws/*`, `/docs*` → `app:8000`,
  остальное → `web:3001`; сертификат Let's Encrypt автоматически по домену.
- `.env` — переменные для compose (`POSTGRES_USER/PASSWORD/DB`).
- `MavixServer.env`, `MavixWeb.env` — env конкретных сервисов (`env_file`).
- `.env.example` — образец.

## Предварительные требования
- VPS с Linux, установленные Docker и Docker Compose.
- Домен с A-записью на IP сервера (в `Caddyfile` — `drone-mavix.ru`); открыты
  порты 80 и 443 (для выпуска TLS-сертификата).

## Установка

```bash
# 1. В этом каталоге клонировать репозитории компонентов рядом с compose:
git clone <MavixServer> MavixServer
git clone <MavixWeb>    MavixWeb

# 2. Положить env-файлы (рядом с docker-compose.yaml):
#    .env            — POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB
#    MavixServer.env — DATABASE_URL, JWT_SECRET, STUN/TURN, EMAIL_SMTP_*, BUILDS_*, WEB_BASE_URL, …
#    MavixWeb.env    — PORT, API_BASE_URL
#    (образец полей — .env.example; реальные секреты в репозиторий НЕ коммитить)

# 3. При необходимости — поправить домен/email в Caddyfile.

# 4. Поднять стек (миграции выполнит сервис migrator):
docker compose up -d --build
docker compose ps
```

## Дистрибутивы клиентов (борт и десктоп)
Сервис `app` монтирует каталоги, откуда отдаёт сборки на скачивание:
- `./MavixServer/wheels` → wheels борта (`/api/v1/builds/board` собирает tar.gz);
- `./MavixServer/prebuilt` → готовые бинари десктопа (.AppImage / .exe).

Собрать и положить сюда — скриптами `StartUp/build_board.sh`,
`build_desktop_linux.sh`, `build_desktop_exe.sh` (печатают команду `scp` на сервер)
либо `StartUp/build/*` (сборка + автоматическая отправка и перезапуск `app`).

## STUN/TURN
Отдельный сервер NAT-traversal ставится скриптом
[`../StunTurn/install_turn_standalone.sh`](../StunTurn/install_turn_standalone.sh).
Параметры TURN прописываются в `MavixServer.env` (`TURN_SERVER`/`TURN_USERNAME`/
`TURN_PASSWORD`, при TLS-варианте — `TURNS_SERVER`) и отдаются клиентам через
`/api/v1/ice-servers`.

## Эксплуатация
```bash
docker compose logs -f app           # логи сервера
docker compose logs -f caddy         # логи TLS-прокси
docker compose exec app alembic upgrade head   # миграции вручную
docker compose up -d --build         # обновление (после git pull в MavixServer/MavixWeb)
docker compose restart app           # перезапуск сервера
```

## Примечания
- За Caddy сервер стоит за обратным прокси — для корректного определения IP
  клиента (rate-limit, логи) задайте `TRUST_PROXY_HEADERS=true` в `MavixServer.env`.
- Env-файлы с реальными секретами держите вне публичного доступа (в репозиторий —
  только `.env.example`).
