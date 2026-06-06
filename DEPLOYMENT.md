# Mavix — развёртывание системы доставки грузов (локально и в прод)

Исчерпывающее руководство: что изменилось, чего ожидать, какие `.env`-файлы
нужны, как поднять весь стек на локальном компьютере и пройти полный сценарий
доставки.

---

## 0. Что изменилось (если вы знали старый Mavix)

Раньше Mavix был системой **FPV-управления дроном** (оператор сам выбирал дрон
из списка и пилотировал). Теперь это **автоматизированная система доставки
малогабаритных грузов** по модели «как в такси». Технологическая база та же
(WebRTC-видео + сигналинг + CRSF/MAVLink), но роли и потоки переработаны.

**Три роли:**

| Роль | Приложение | Как заходит |
|---|---|---|
| **Администратор** | MavixWeb (веб-кабинет) | регистрируется/логинится сам (email+пароль) |
| **Оператор** | MavixDesktop-UI | логин+пароль выдаёт администратор |
| **Дрон** | MavixBoard (Raspberry Pi) | саморегистрируется при первом запуске |

**Главные изменения по компонентам:**

- **MavixServer** — таблица `users`→`admins`; новые `operators`, `deliveries`;
  роль в JWT (admin/operator); `/auth/operator/login`; CRUD операторов;
  **саморегистрация дрона** `POST /drones/enroll` по `ENROLLMENT_TOKEN`
  (не JWT); сборка board-tarball теперь **одна на админа** (вшиваются
  `ADMIN_ID`+`ENROLLMENT_TOKEN`, без `DRONE_ID`); REST доставок + state-machine
  с атомарным «такси»-приёмом; WS: `/ws/gcs` теперь для оператора, новый
  `/ws/admin` для уведомлений; нотификатор `delivery_offer/accepted/delivered`.
- **MavixBoard** — при первом запуске сам генерирует `DRONE_ID`,
  регистрируется и дописывает токен/имя в `.env`; шлёт GPS/курс по
  **выделенному telemetry data-channel**.
- **MavixWeb** — админ-панель: операторы, дроны, доставки (с картой Leaflet),
  WS-уведомления; публичная страница скачивания desktop; ребрендинг под доставку.
- **MavixDesktop-UI** — вход оператора; вместо списка дронов — экран ожидания
  заявок; уведомление-заявка с кнопкой «Принять»; карта (Leaflet в
  QWebEngineView, вращается по курсу); кнопка «Сброс груза» (AUX-канал CH8 +
  отметка доставки).

**Чего ожидать после развёртывания:** админ заходит в веб → заводит операторов
и скачивает ПО для дрона → дроны сами появляются в кабинете → админ создаёт
заявку → подключённый оператор в desktop видит её, принимает, видит видео +
карту, летит, жмёт «Сброс груза» → админу прилетает «доставлено».

**Ветки:** эталонный FPV-проект заморожен в `remote_control`, вся новая
разработка — в `delivery_control` (текущая). Все компоненты подключены к
родительскому репозиторию `Mavix` как git-submodule на ветке `delivery_control`.

---

## 1. Требования

- **git** (с поддержкой submodule).
- **Docker** + **Docker Compose v2** (для сервера и БД).
- **Node.js 18+** и **npm** (для MavixWeb, если запускаете без Docker).
- **Python 3.11+** (для запуска MavixBoard/MavixDesktop из исходников и тестов).
- Для **MavixDesktop** карта/видео требуют системных библиотек: `libGL`,
  Qt WebEngine, ffmpeg/SDL (см. §7).

---

## 2. Клонирование (с submodule)

```sh
git clone --recurse-submodules -b delivery_control https://github.com/AurunChill/Mavix.git
cd Mavix
# если клонировали без --recurse-submodules:
git submodule update --init --recursive
# подтянуть свежие коммиты submodule на их ветке delivery_control:
git submodule update --remote --merge
```

Структура:

```
Mavix/
├── MavixServer/        (submodule, AurunChill/MavixServer @ delivery_control)
├── MavixBoard/         (submodule, AurunChill/MavixBoard @ delivery_control)
├── MavixWeb/           (submodule, dexstronggg/MavixWeb @ delivery_control)
├── MavixDesktop-UI/    (submodule, dexstronggg/MavixDesktop-UI @ delivery_control)
├── ForServer/          (конфиги прод-развёртки: docker-compose, Caddy, coturn)
├── PLAN.md             (план переделки)
└── DEPLOYMENT.md       (этот файл)
```

---

## 3. Конфигурация — какие `.env`-файлы нужны

`.env` нигде не коммитятся (в `.gitignore`). Создавайте из `*.example`.

### 3.1 `MavixServer/.env` — главный конфиг (копировать из `MavixServer/.env.example`)

```env
# --- Сервер ---
HOST=0.0.0.0
PORT=8000
RPM=60

# --- БД (для docker-compose локально) ---
POSTGRES_USER=mavix
POSTGRES_PASSWORD=mavix_local_pw
POSTGRES_DB=mavix
DATABASE_URL=postgresql+asyncpg://mavix:mavix_local_pw@db:5432/mavix

# --- JWT (ОБЯЗАТЕЛЬНО сменить, минимум 32 символа) ---
JWT_SECRET=сгенерируйте_через_python_-c_"import secrets;print(secrets.token_urlsafe(48))"
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=30

# --- WebRTC ICE (для локали хватит публичного STUN) ---
STUN_SERVER=stun:stun.l.google.com:19302
TURN_SERVER=
TURN_USERNAME=
TURN_PASSWORD=

# --- WebSocket ---
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=45
WS_HANDSHAKE_CAPACITY=5
WS_HANDSHAKE_REFILL_PER_SEC=0.5
WS_AUTH_TIMEOUT=5
WS_AUTH_REFRESH_WARNING_SECONDS=60

# --- CORS: ОБЯЗАТЕЛЬНО добавить origin веб-кабинета ---
CORS_ALLOW_ORIGINS=http://localhost:3001

# --- Очистка неактивных дронов ---
CLEANUP_ENABLED=true
CLEANUP_INTERVAL_HOURS=24
CLEANUP_DRONE_INACTIVE_DAYS=30

# --- Раздача сборок ---
BUILDS_ENABLED=true
BUILDS_TEMPLATE_DIR=/srv/mavix/build-templates
BUILDS_WHEELS_DIR=/srv/mavix/wheels
BUILDS_CACHE_DIR=/var/cache/mavix/builds
BUILDS_PREBUILT_DIR=/srv/mavix/prebuilt
# КРИТИЧНО: адрес, на который board будет стучаться. Для локали — где доступен
# сервер с точки зрения дрона (НЕ localhost, если дрон на другой машине!).
BUILDS_SIGNAL_SERVER_URL=http://localhost:8000

# --- Email (нужен для писем: welcome / сброс пароля / новый дрон) ---
EMAIL_SMTP_HOST=smtp.yandex.com
EMAIL_SMTP_PORT=465
EMAIL_SMTP_USE_TLS=true
EMAIL_SMTP_USERNAME=your-address@yandex.com
EMAIL_SMTP_PASSWORD=app_password
EMAIL_FROM_ADDRESS=your-address@yandex.com
EMAIL_FROM_NAME=Mavix UAV

# --- Базовый URL веба (для ссылок в письмах) ---
WEB_BASE_URL=http://localhost:3001
```

> ⚠️ **JWT_SECRET**: сервер откажется стартовать, если оставить значение из
> примера или короче 32 символов (защита от утечки общего секрета).
>
> ⚠️ **Email**: при регистрации админа и саморегистрации дрона сервер шлёт
> письма. Укажите рабочий SMTP (для Яндекс — пароль приложения). Если письма
> не нужны на локали — задайте любой валидный SMTP или используйте mailtrap-
> подобный сервис; иначе соответствующие операции могут падать.

### 3.2 `MavixWeb/.env` (копировать из `MavixWeb/.env.example`)

```env
PORT=3001
# Адрес MavixServer без /api/v1 — клиент добавляет сам.
API_BASE_URL=http://localhost:8000
```

### 3.3 Прод (полный стек через `ForServer/Main`)

`ForServer/Main/` содержит prod-compose со всем стеком (db + migrator + app +
web + Caddy с TLS). Там лежат примеры:
- `ForServer/Main/.env` — `POSTGRES_USER/PASSWORD/DB` для docker-compose.
- `ForServer/Main/MavixServer.env` — копия §3.1 с прод-значениями (домен,
  реальный TURN, SMTP).
- `ForServer/Main/MavixWeb.env` — `PORT=3001`, `API_BASE_URL=https://<домен>`.
- `ForServer/Main/Caddyfile` — TLS reverse-proxy: `/api`,`/ws`,`/docs` → app,
  остальное → web; Let's Encrypt на домен.

### 3.4 `MavixBoard/.env` (только для запуска board из ИСХОДНИКОВ на dev-машине)

На реальном дроне `.env` нет — всё в `/etc/mavixboard/preset.env`, который
кладёт `install.sh` из tarball. Для dev-прогона board локально:

```env
SIGNAL_SERVER_IP=http://localhost:8000
ADMIN_ID=<admin_id из веб-кабинета>
ENROLLMENT_TOKEN=<enrollment_token админа>
# DRONE_ID/DRONE_TOKEN/DRONE_NAME появятся сами после первой саморегистрации
```

### 3.5 `MavixDesktop-UI/.env` (для запуска desktop из ИСХОДНИКОВ; копия из `.env-example`)

```env
SIGNAL_URL=http://localhost:8000
# опц. переопределения:
# SIGNAL_WS_URL=ws://localhost:8000/ws/gcs
# STUN_SERVER=stun:stun.l.google.com:19302
# TURN_SERVER=
```

У установленного desktop настройки лежат в `~/.config/mavixdesktop/config.json`
и правятся через кнопку настроек в самом приложении.

---

## 4. Локальный запуск — сервер + БД + веб

### 4.1 Сервер и БД (Docker Compose)

```sh
cd MavixServer
cp .env.example .env          # отредактировать по §3.1
# Собрать wheels для board-tarball (нужно для скачивания ПО дрона):
./scripts/build_wheels.sh ../MavixBoard      # кладёт ~15 МБ в wheels/board/
docker compose up --build -d                  # поднимет db → migrator (alembic) → app
curl http://localhost:8000/api/v1/health      # {"status":"ok"}
# Swagger: http://localhost:8000/docs
```

`docker compose` автоматически: поднимает Postgres 16, прогоняет миграции
Alembic (`migrator`), запускает FastAPI (`app`) на :8000.

### 4.2 Веб-кабинет

Вариант A — локально через Node:

```sh
cd MavixWeb
cp .env.example .env          # PORT=3001, API_BASE_URL=http://localhost:8000
npm install
npm start                     # http://localhost:3001
```

Вариант B — в Docker (есть `MavixWeb/Dockerfile`/`docker-compose.yaml`).

> Веб-origin (`http://localhost:3001`) обязан быть в `CORS_ALLOW_ORIGINS`
> сервера (§3.1), иначе браузер заблокирует запросы.

### 4.3 Полный стек одной командой (прод-подобно)

```sh
cd ForServer/Main
cp .env.example .env
# заполнить MavixServer.env и MavixWeb.env (см. §3.3)
docker compose up -d          # db + migrator + app + web + caddy
```

---

## 5. Первый сценарий (проверка работоспособности)

1. **Регистрация админа**: открыть `http://localhost:3001/register`, создать
   аккаунт (email+пароль). Войти.
2. **Скачать ПО для дрона**: кабинет → «Дроны» → «Скачать ПО (.tar.gz)».
   Архив содержит `ADMIN_ID`+`ENROLLMENT_TOKEN` этого админа (один на все дроны).
3. **Установить на дрон** (Raspberry Pi, см. §6) → при первом запуске дрон сам
   зарегистрируется и появится в «Дроны» с именем (напр. «весёлый-кит»).
4. **Завести оператора**: кабинет → «Операторы» → создать (ФИО, паспорт,
   адрес). Система покажет сгенерированные **username и password — один раз**,
   скопируйте их.
5. **Передать оператору**: ссылку на desktop (`http://localhost:3001/download/desktop`,
   публичная) + выданные логин/пароль.
6. **Оператор входит в desktop** (см. §7) этими кредами → попадает на экран
   ожидания заявок.
7. **Создать заявку**: кабинет → «Доставки» → выбрать дрон, указать адрес/точку
   на карте, опц. груз → создать. Заявка рассылается онлайн-операторам админа.
8. **Оператор принимает** → видит видео с дрона + карту (вращается по курсу) →
   пилотирует.
9. **Сброс груза**: в полёте оператор жмёт «Сброс груза» (кнопка/назначенная в
   калибровке кнопка джойстика) → CH8 уходит на FC → груз сброшен → доставка
   `delivered` → админу приходит уведомление.
10. **Журнал**: кабинет → «Доставки» — статусы и история.

---

## 6. MavixBoard на Raspberry Pi

Полная подготовка RPi (ОС, UART, камеры, FC) — в `MavixBoard/README.md` и
`MavixBoard/USER_GUIDE.md`. Кратко для уже подготовленной RPi:

```sh
# скачать tarball из веб-кабинета (Дроны → Скачать ПО), скопировать на RPi:
scp mavixboard-XXXXXXXX.tar.gz rpi@mavixboard.local:~
ssh rpi@mavixboard.local
tar -xzf mavixboard-*.tar.gz && cd mavixboard-*
sudo ./install.sh                         # ставит venv + wheels + systemd-юнит
sudo systemctl enable --now mavixboard    # автозапуск
journalctl -u mavixboard -f               # логи; увидите [enroll] зарегистрирован drone_id=...
```

Дев-запуск из исходников (на любой Linux-машине):

```sh
cd MavixBoard
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"                   # требует системный GStreamer + PyGObject
cp .env-example .env                      # заполнить ADMIN_ID/ENROLLMENT_TOKEN (§3.4)
python -m mavixboard
```

---

## 7. MavixDesktop-UI (оператор)

### Запуск из исходников

```sh
cd MavixDesktop-UI
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp .env-example .env                      # SIGNAL_URL=http://localhost:8000
python -m mavixdesktop                    # GUI; войти кредами оператора
```

**Системные зависимости** (Ubuntu/Debian): для GUI/видео/карты нужны
`libgl1`, `libglx-mesa0`, Qt WebEngine (тянется с PySide6), ffmpeg-библиотеки
(для PyAV), SDL (для pygame):

```sh
sudo apt install -y libgl1 libglib2.0-0 libegl1 libxcb-cursor0
```

> **Карта** работает через `QWebEngineView` + Leaflet (CDN). Для сборки
> PyInstaller QtWebEngine собирается через `mavixdesktop.spec` (уже настроено).

### Сборка дистрибутивов

```sh
cd MavixDesktop-UI/scripts
./build_appimage.sh        # Linux AppImage
./build_binary.sh          # Linux single-file
# build_windows.ps1        # Windows .exe (на Windows)
```

Готовые бинари кладутся на сервер в `BUILDS_PREBUILT_DIR` или в
`MavixWeb/public/downloads/` (откуда их отдаёт публичная страница).

---

## 8. STUN/TURN (для связи через NAT / интернет)

Локально (обе стороны в одной сети) хватает STUN. Для реального интернета
поднимите coturn — скрипт `ForServer/StunTurn/install_turn_standalone.sh`
(Ubuntu, отдельный сервер с доменом). После установки пропишите в
`MavixServer/.env`: `TURN_SERVER`, `TURNS_SERVER`, `TURN_USERNAME`,
`TURN_PASSWORD` и перезапустите `app`.

---

## 9. Тесты

Все компоненты зелёные. Как прогнать:

```sh
# MavixServer (Python, pytest)
cd MavixServer && python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]" && pytest          # 341 passed (ws-тесты ретраятся через rerunfailures)

# MavixBoard
cd MavixBoard && pip install -e ".[dev]" && pytest    # 298 passed (gi мокается)

# MavixWeb (Jest)
cd MavixWeb && npm install && npm test      # 40 passed

# MavixDesktop-UI (pytest + pytest-qt, offscreen)
cd MavixDesktop-UI && pip install -e ".[dev]"
QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy pytest   # 236 passed (нужен libGL в системе)
```

> На headless-машине без libGL desktop GUI-тесты не импортируются. Поставьте
> `libgl1` (`sudo apt install libgl1`) — этого достаточно для offscreen-прогона.

---

## 10. Траблшутинг

| Симптом | Причина / решение |
|---|---|
| `app` не стартует, `InsecureConfiguration` | `JWT_SECRET` из примера/короче 32 — задайте свой |
| Браузер: CORS-ошибка к API | добавьте origin веба в `CORS_ALLOW_ORIGINS` сервера |
| Дрон не появляется в кабинете | проверьте `ADMIN_ID`/`ENROLLMENT_TOKEN` в preset.env и `BUILDS_SIGNAL_SERVER_URL` (дрон должен достучаться до сервера) |
| Скачивание ПО дрона 503/500 | не собраны wheels: `./scripts/build_wheels.sh ../MavixBoard` |
| Оператор не видит заявку | оператор должен быть онлайн в desktop (подключён к `/ws/gcs`) и принадлежать тому же админу |
| Desktop падает на старте (libGL) | `sudo apt install libgl1 libegl1 libxcb-cursor0` |
| WebRTC не поднимается через интернет | настройте TURN (§8) |
| Регистрация/письма падают | проверьте SMTP в `MavixServer/.env` |

---

## 11. Полезные ссылки внутри репозитория

- `PLAN.md` — что и почему переделано (архитектура, модель данных, решения).
- `MavixServer/TECHNICAL.md`, `MavixServer/README.md` — API и БД.
- `MavixBoard/README.md`, `USER_GUIDE.md` — подготовка RPi, UART, FC, камеры.
- `MavixDesktop-UI/scripts/README.md` — сборка дистрибутивов.
- `ForServer/Main/README.md` — прод-развёртка.
- Swagger API: `http://localhost:8000/docs`.
