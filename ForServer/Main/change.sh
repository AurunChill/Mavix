#!/usr/bin/env bash
# change.sh — переключение MavixServer + MavixWeb между ветками
# delivery/remote с сохранением и восстановлением БД отдельно для каждой ветки.
#
# Зачем: схемы БД у веток разные (delivery: admins/operators/deliveries,
# remote: users), поэтому при переключении БД нужно пересоздавать. Чтобы не
# терять данные, перед сбросом снимается дамп текущей ветки, а после
# переключения подгружается ранее сохранённый дамп целевой ветки. У каждой
# ветки — свой снимок в ./dumps/<ветка>.sql.
#
# Использование (запускать из каталога с docker-compose.yaml):
#   ./change.sh --branch delivery     # → delivery_control
#   ./change.sh --branch remote       # → remote_control
# Доп. флаги:
#   --no-build   не пересобирать образы (быстрее, если код уже собран)
#   -y | --yes   не спрашивать подтверждение
#
# Шаги:
#   1. Поднять db, снять дамп текущей БД в dumps/<текущая-ветка>.sql.
#   2. Остановить app/web/migrator; переключить MavixServer и MavixWeb на
#      целевую ветку (checkout + ff-pull).
#   3. Пересобрать образы.
#   4. УДАЛИТЬ БД (drop database) и создать пустую.
#   5. Если есть dumps/<целевая-ветка>.sql — восстановить его.
#   6. Поднять весь стек (migrator при необходимости домигрирует).

set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

#### аргументы #########################################################################
TARGET=""
NO_BUILD=0
ASSUME_YES=0
while [ $# -gt 0 ]; do
  case "$1" in
    --branch)    TARGET="${2:-}"; shift 2;;
    --branch=*)  TARGET="${1#*=}"; shift;;
    --no-build)  NO_BUILD=1; shift;;
    -y|--yes)    ASSUME_YES=1; shift;;
    -h|--help)   grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "неизвестный аргумент: $1 (нужно --branch delivery|remote)" >&2; exit 2;;
  esac
done

case "$TARGET" in
  delivery|delivery_control) GIT_BRANCH=delivery_control;;
  remote|remote_control)     GIT_BRANCH=remote_control;;
  *) echo "укажите ветку: --branch delivery | --branch remote" >&2; exit 2;;
esac

#### окружение #########################################################################
[ -f ./docker-compose.yaml ] || [ -f ./docker-compose.yml ] || {
  echo "ОШИБКА: запускайте из каталога с docker-compose.yaml" >&2; exit 1; }
[ -f ./.env ] || { echo "ОШИБКА: нет ./.env с POSTGRES_*" >&2; exit 1; }
set -a; . ./.env; set +a
PGUSER="${POSTGRES_USER:?нет POSTGRES_USER в .env}"
PGDB="${POSTGRES_DB:?нет POSTGRES_DB в .env}"

if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi

DUMP_DIR=./dumps
SERVER_DIR=./MavixServer
WEB_DIR=./MavixWeb
mkdir -p "$DUMP_DIR"
[ -d "$SERVER_DIR/.git" ] || { echo "ОШИБКА: $SERVER_DIR — не git-репозиторий" >&2; exit 1; }
[ -d "$WEB_DIR/.git" ]    || { echo "ОШИБКА: $WEB_DIR — не git-репозиторий" >&2; exit 1; }

CUR_BRANCH=$(git -C "$SERVER_DIR" rev-parse --abbrev-ref HEAD)

echo "── change.sh ───────────────────────────────────────────"
echo "  текущая ветка server : $CUR_BRANCH"
echo "  целевая ветка        : $GIT_BRANCH"
echo "  каталог дампов       : $DUMP_DIR"
echo "────────────────────────────────────────────────────────"
if [ "$ASSUME_YES" -ne 1 ]; then
  printf "Продолжить? БД '%s' будет пересоздана (текущая сохранится в дамп). [y/N] " "$PGDB"
  read -r ans; case "$ans" in y|Y|yes|да) ;; *) echo "отмена"; exit 0;; esac
fi

#### helpers ###########################################################################
wait_db_healthy() {
  echo "  · жду готовности БД…"
  for _ in $(seq 1 30); do
    if $DC exec -T db pg_isready -U "$PGUSER" -d postgres >/dev/null 2>&1; then return 0; fi
    sleep 2
  done
  echo "ОШИБКА: БД не поднялась" >&2; return 1
}
db_has_database() {
  $DC exec -T db psql -U "$PGUSER" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='$PGDB'" 2>/dev/null | grep -q 1
}

#### 1. поднять db и снять дамп текущей ветки #########################################
echo "  · поднимаю db"
$DC up -d db
wait_db_healthy
if db_has_database; then
  echo "  · дамп текущей БД → $DUMP_DIR/$CUR_BRANCH.sql"
  $DC exec -T db pg_dump -U "$PGUSER" -d "$PGDB" --no-owner --no-privileges \
    > "$DUMP_DIR/$CUR_BRANCH.sql"
else
  echo "  · БД '$PGDB' ещё нет — дамп пропущен"
fi

#### 2. остановить сервисы и переключить ветки #######################################
echo "  · останавливаю app/web/migrator"
$DC stop app web migrator >/dev/null 2>&1 || true

switch_repo() {
  local dir="$1"
  echo "  · $dir → $GIT_BRANCH"
  git -C "$dir" fetch origin "$GIT_BRANCH" --quiet || true
  git -C "$dir" checkout "$GIT_BRANCH"
  git -C "$dir" pull --ff-only origin "$GIT_BRANCH" --quiet \
    || echo "    (ff-pull не выполнен — оставляю локальную $GIT_BRANCH)"
}
switch_repo "$SERVER_DIR"
switch_repo "$WEB_DIR"

#### 3. пересборка образов ###########################################################
if [ "$NO_BUILD" -ne 1 ]; then
  echo "  · пересобираю образы (app/web/migrator)"
  $DC build app web migrator
fi

#### 4. удалить и пересоздать БД #####################################################
echo "  · удаляю БД '$PGDB' и создаю пустую"
$DC exec -T db psql -U "$PGUSER" -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS \"$PGDB\" WITH (FORCE);" \
  -c "CREATE DATABASE \"$PGDB\" OWNER \"$PGUSER\";"

#### 5. восстановить дамп целевой ветки ##############################################
if [ -f "$DUMP_DIR/$GIT_BRANCH.sql" ]; then
  echo "  · восстанавливаю $DUMP_DIR/$GIT_BRANCH.sql"
  $DC exec -T db psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 \
    < "$DUMP_DIR/$GIT_BRANCH.sql"
else
  echo "  · дампа для $GIT_BRANCH нет — стартую с чистой БД (миграции создадут схему)"
fi

#### 6. поднять весь стек ############################################################
echo "  · поднимаю весь стек (migrator → app → web → caddy)"
$DC up -d --build
echo "── готово: $CUR_BRANCH → $GIT_BRANCH ──────────────────────"
echo "  логи сервера: $DC logs -f app"
