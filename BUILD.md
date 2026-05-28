# Mavix — сборка и релиз

Шпаргалка по тому, как собирать и публиковать все артефакты. Если ты
вернулся к проекту через полгода и не помнишь, что где — открой этот
файл и иди по разделам сверху вниз.

---

## 0. Структура проекта

Рабочие репозитории лежат в `~/Projects/Mavix/`:

| Каталог              | Что это                                          | Релизный артефакт                              |
|----------------------|--------------------------------------------------|------------------------------------------------|
| `MavixServer/`       | FastAPI + PostgreSQL backend, в Docker. Signal-server для WebRTC, раздаёт сборки клиентов. | Docker-образ (билдится из репы). Сам файл `.deb`/AppImage наружу не отдаёт — генерит или раздаёт чужие. |
| `MavixWeb/`          | Лендинг + личный кабинет (Express + vanilla JS). | Express-сервер (поднимается отдельно). Скачивания идут через API MavixServer. |
| `MavixDesktop-UI/`   | PySide6 GUI оператора (главное приложение).      | PyInstaller single-file: `mavixdesktop-linux` (выдаётся под именем `.AppImage`) и `mavixdesktop.exe`. |
| `MavixBoard/`        | Python-софт для Raspberry Pi на дроне.           | wheel-ы (статика на сервере); сервер собирает per-drone `.tar.gz` при скачивании. |

`MavixDesktop/` (без `-UI`) — **старая версия**, не использовать.

---

## 1. `.env`-файлы — где что и кто их читает

Самое частое место путаницы. Карта:

| Файл                                         | Кто читает                  | Что в нём                                                    |
|----------------------------------------------|------------------------------|--------------------------------------------------------------|
| `MavixServer/.env`                           | контейнер `app`, миграции    | DB creds, SMTP, JWT секрет, `BUILDS_SIGNAL_SERVER_URL`, STUN/TURN credentials для WebRTC, `CORS_ALLOW_ORIGINS`. **Это главный конфиг — всё остальное от него зависит.** |
| `MavixServer/.env.example`                   | человек, который раскатывает | Шаблон для `.env` — копируется в `.env` при первой раскатке. |
| `MavixDesktop-UI/.env-example`               | разработчик                  | Пример dev-настроек desktop. Реальный `.env` рядом с этим файлом нужен ТОЛЬКО при запуске из исходников. |
| `~/.config/mavixdesktop/config.json`         | установленный desktop        | JSON с настройками, который правится через **Settings UI** в самом приложении. Это то, что юзер реально меняет. |
| `MavixBoard/.env`                            | разработчик                  | Только для запуска board локально из исходников. На реальной RPi его нет. |
| `/etc/mavixboard/preset.env`                 | systemd / venv-процесс       | Создаётся **сервером** при сборке tarball для конкретного дрона. Содержит per-drone `USER_ID`/`DRONE_TOKEN`/`DRONE_ID` + `SIGNAL_SERVER_IP`. Юзер его руками не правит. |

### Что попадает в `preset.env` дрона

Сервер берёт значения из **двух источников**:

1. **Per-drone (из БД, генерится автоматически)**:
   - `USER_ID` — id залогиненного пользователя.
   - `DRONE_ID` — генерируется при каждом скачивании (32 hex).
   - `DRONE_TOKEN` — генерируется вместе с дроном (64 hex).

2. **Общее (из `MavixServer/.env`)**:
   - `SIGNAL_SERVER_IP` ← `BUILDS_SIGNAL_SERVER_URL`. **Это критично:** именно сюда дрон будет стучаться. `localhost:8000` — только для теста на той же машине; для прода — реальный публичный URL.

Шаблон со статичными значениями (STUN/TURN дефолты для дрона и т.п.)
лежит в `MavixServer/build-templates/board/preset.env.template` —
правится руками, попадает в архив. Изменения шаблона **инвалидируют
кэш**, новые скачивания получают свежий файл автоматически.

### Что попадает в desktop config

PyInstaller-бинарь несёт **дефолты из кода** (`core/config.py`). При
первом запуске приложение создаёт `~/.config/mavixdesktop/config.json`
с этими дефолтами. Дальше юзер правит JSON через **Settings UI в
приложении** (шестерёнка в шапке).

Чтобы поменять prod-дефолты — отредактируй значения по умолчанию в
`MavixDesktop-UI/src/mavixdesktop/core/config.py` и пересобери бинарь.
Установленные у юзеров не обновятся автоматически; они продолжат
работать с тем JSON, который у них уже есть, но новые установки
получат новые дефолты.

---

## 2. MavixServer — общая раскатка

### Первый запуск

```sh
cd ~/Projects/Mavix/MavixServer
cp .env.example .env
# отредактировать .env: JWT_SECRET, DB creds, BUILDS_SIGNAL_SERVER_URL,
# SMTP, STUN/TURN, CORS_ALLOW_ORIGINS — см. комментарии в файле
./scripts/build_wheels.sh ../MavixBoard       # ~15 МБ wheels для board
docker compose up --build -d
curl http://localhost:8000/api/v1/health      # {"status":"ok"}
```

### Что мониторится в `MavixServer/`

| Каталог            | Зачем                                                | Монтируется в контейнер как |
|--------------------|------------------------------------------------------|------------------------------|
| `wheels/board/`    | Wheels для board tarball, кладёт `build_wheels.sh`.  | `/srv/mavix/wheels:ro`       |
| `prebuilt/`        | Заранее собранные desktop-бинари (Linux + .exe).     | `/srv/mavix/prebuilt:ro`     |
| `build-templates/` | Шаблоны для board tarball (`install.sh.template`, `preset.env.template`, `mavixboard.service.template`). | Копируется в образ при `docker build`. |
| `build_cache` (volume) | Кэш собранных `.tar.gz` board под per-drone hash. | `/var/cache/mavix/builds`   |

### Когда что нужно

| Изменилось                            | Что сделать                                          |
|---------------------------------------|------------------------------------------------------|
| Питон-код сервера (src/, alembic/)    | `docker compose build app && docker compose up -d`   |
| `.env` сервера                        | `docker compose restart app`                         |
| `build-templates/*` (шаблоны board)   | `docker compose build app` (попадает в образ)        |
| `wheels/board/`                       | Ничего, монтируется live. Скачивание подхватит автоматически (кэш инвалидируется по хешу wheel'ов). |
| `prebuilt/mavixdesktop-linux` или `.exe` | `docker compose restart app` (FileResponse читает с диска, рестарт не строго нужен, но безопаснее). |

### Сброс кэша board tarball

Кэш живёт в named volume `mavixserver_build_cache`. Сбросить:

```sh
docker compose down
docker volume rm mavixserver_build_cache
docker compose up -d
```

В норме делать не надо: кэш-ключ включает хеш всех шаблонов, wheel'ов
и per-drone значений — изменение любого из этого автоматически даёт
новый ключ.

---

## 3. MavixBoard — что собирать на сервере

Сам клиент board собирается **на сервере**, на лету, при скачивании.
Тебе нужно только:

### 3.1. Wheels (один раз на релиз)

```sh
cd ~/Projects/Mavix/MavixServer
./scripts/build_wheels.sh ../MavixBoard
```

Скрипт делает `pip wheel` со всеми транзитивными зависимостями. Результат — `wheels/board/*.whl`. Размер ~15 МБ.

**Важно:** wheels собираются под **архитектуру хоста**. Если хост
x86_64, а дрон — RPi (aarch64), бинарные wheels не совпадут. Варианты:

- Запустить `build_wheels.sh` на RPi и закинуть результат на сервер.
- Или `pip wheel --platform manylinux2014_aarch64 --only-binary=:all:` — работает не всегда.

Для board сейчас почти все зависимости pure-Python, проблема в основном
с `pymavlink` (есть `.so`).

### 3.2. Шаблоны

Лежат в `MavixServer/build-templates/board/`:

- `preset.env.template` — конфиг для дрона. `{{USER_ID}}`, `{{DRONE_ID}}`, `{{DRONE_TOKEN}}`, `{{SIGNAL_SERVER_IP}}` подставляются сервером. Остальные значения (STUN/TURN дефолты, `SIGNAL_WS_URL`) — статика, правится руками.
- `install.sh.template` — установщик. Ставит apt-deps (GStreamer, python3-gi), делает venv, ставит wheels офлайн, кладёт `preset.env` в `/etc/mavixboard/`, кладёт systemd unit (но **не enable**-ит).
- `mavixboard.service.template` — systemd unit. После установки лежит в `/etc/systemd/system/mavixboard.service`.

Изменил шаблон — нужен `docker compose build app`, потому что шаблоны
копируются в образ при сборке.

### 3.3. Что делает пользователь после скачивания

```sh
tar xzf mavixboard-XXXXXXXX.tar.gz
cd mavixboard-XXXXXXXX
sudo ./install.sh
```

**Ручной запуск** (для теста — что приехало в `preset.env`):
```sh
set -a; . /etc/mavixboard/preset.env; set +a
sudo /opt/mavixboard/.venv/bin/python -m mavixboard
```

**Автозапуск** (по желанию):
```sh
sudo systemctl enable --now mavixboard
sudo journalctl -u mavixboard -f
```

---

## 4. MavixDesktop — Linux (single-file binary)

PyInstaller `--onefile` с расширением `.AppImage`. По факту это
portable executable, для юзера ведёт себя как AppImage:
`chmod +x`, двойной клик.

### Требования

- Linux x86_64 (или ту же архитектуру, на которой будут юзеры).
- Python 3.12+, `pip`, `venv`.
- PyInstaller.

### Сборка

```sh
cd ~/Projects/Mavix/MavixDesktop-UI
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pyinstaller
./scripts/build_binary.sh
```

Результат: `dist/mavixdesktop-linux` (~150 МБ).

### Публикация

```sh
cp dist/mavixdesktop-linux \
   ~/Projects/Mavix/MavixServer/prebuilt/mavixdesktop-linux
cd ~/Projects/Mavix/MavixServer
docker compose restart app
```

После рестарта эндпойнт `GET /api/v1/builds/desktop?build_type=deb`
будет отдавать свежий бинарь под именем `mavixdesktop-linux.AppImage`.

### Заметки

- Бинарь привязан к **glibc** хоста сборки. Билдь на относительно
  старой системе (Ubuntu 22.04 / 24.04) для совместимости, не на
  bleeding-edge.
- Бинарь привязан к **архитектуре**. x86_64-бинарь не запустится на ARM.

---

## 5. MavixDesktop — Windows (.exe)

Сборка делается на **Windows-машине**. Linux Wine не годится для
PySide6 / aiortc.

### Команды для Windows-человека (PowerShell)

```powershell
git clone https://github.com/dexstronggg/MavixDesktop-UI
cd MavixDesktop-UI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install pyinstaller
pyinstaller mavixdesktop.spec
```

Результат: `dist\mavixdesktop.exe` (~200–300 МБ).

### Подсказки человеку

- Python 3.12 с https://python.org, при установке **отметить «Add Python to PATH»**.
- Если pip ругается на «Microsoft Visual C++ 14.0 or greater is required» — поставить **Microsoft C++ Build Tools** с https://visualstudio.microsoft.com/visual-cpp-build-tools/, в инсталляторе включить «Desktop development with C++».
- Антивирус (Defender, Касперский) может ругаться на PyInstaller `.exe` — это **false positive** из-за стандартного бутлоадера PyInstaller. Добавить в исключения.

### Публикация

Получаешь от Windows-человека `mavixdesktop.exe`. Дальше — **две команды**,
больше ничего трогать не нужно (ни код сервера, ни код веба):

```sh
cp mavixdesktop.exe ~/Projects/Mavix/MavixServer/prebuilt/mavixdesktop.exe
cd ~/Projects/Mavix/MavixServer && docker compose restart app
```

**Почему так просто:**

- Эндпойнт `GET /api/v1/builds/desktop?build_type=exe` уже знает, откуда
  читать файл (`/srv/mavix/prebuilt/mavixdesktop.exe` — монтируется
  из локального `prebuilt/`).
- Кнопка «Windows (.exe)» на странице `/dashboard/software` уже ходит
  на этот эндпойнт. Никаких правок фронта.
- До тех пор, пока `prebuilt/mavixdesktop.exe` не существует, эндпойнт
  возвращает 404 и фронт честно пишет «Сборка ещё не загружена на
  сервер». Как только файл появляется — кнопка начинает работать
  без задержки.

То же относится к Linux-бинарю (`mavixdesktop-linux`): обновлять = просто
заменить файл в `prebuilt/` + `docker compose restart app`. Сервер и веб
о новых релизах ничего знать не должны.

---

## 6. MavixWeb

Express + vanilla JS. Поднимается отдельно от MavixServer (на 3001 по
умолчанию). Скачивания идут через API MavixServer — MavixWeb сам
никакие сборки не отдаёт.

Запуск:
```sh
cd ~/Projects/Mavix/MavixWeb
npm install
npm start
```

Если меняешь HTML/JS в `public/` — рестарт не нужен, статика читается
с диска.

---

## 7. STUN / TURN

Отдельный coturn сервер, обычно крутится на отдельной VM. См. конфиг
`docker-compose.yaml` + `turnserver.conf` (история чата). В MavixServer
прописаны креды:

```
STUN_SERVER=stun:HOST:3478
TURN_SERVER=turn:HOST:3478
TURN_USERNAME=...
TURN_PASSWORD=...
```

Сервер раздаёт их клиентам через `GET /api/v1/ice-servers`. Меняешь —
`docker compose restart app`.

---

## 8. Релизный checklist

Когда катишь свежий релиз:

1. **MavixBoard wheels:**
   ```sh
   cd ~/Projects/Mavix/MavixServer
   ./scripts/build_wheels.sh ../MavixBoard
   ```
2. **MavixDesktop Linux:**
   ```sh
   cd ~/Projects/Mavix/MavixDesktop-UI
   ./scripts/build_binary.sh
   cp dist/mavixdesktop-linux ../MavixServer/prebuilt/mavixdesktop-linux
   ```
3. **MavixDesktop Windows:** дать команды Windows-человеку (см. раздел 5), получить `.exe`, положить в `MavixServer/prebuilt/mavixdesktop.exe`.
4. **Сервер:**
   ```sh
   cd ~/Projects/Mavix/MavixServer
   # если менялся код сервера или build-templates:
   docker compose up --build -d
   # если менялись только wheels/prebuilt:
   docker compose restart app
   ```
5. **Проверка:**
   ```sh
   curl http://localhost:8000/api/v1/health
   # скачать через UI (/dashboard/software) и убедиться, что файлы
   # валидные и устанавливаются.
   ```
6. **На реальной машине** проверить, что MavixDesktop запускается и
   видит сервер, а board после `install.sh` подключается.

---

## 9. Раскатка на VPS

### 9.1. Архитектура

На одной VPS поднимаются:

- **db** (postgres:16-alpine) — внутри docker-network, не торчит наружу.
- **migrator** — alembic upgrade head, отрабатывает и выходит.
- **app** (MavixServer) — порт `8000`.
- **web** (MavixWeb) — порт `3001`.
- **coturn** — отдельный compose-проект (см. ниже), порт `3478` UDP+TCP и диапазон `49152-65535/udp`.
- **caddy** (опционально) — `80` + `443`, TLS-фронт. Включается, когда домен резолвится.

Главный compose-файл лежит в корне `Mavix/` и подтягивает оба репа
(`MavixServer/`, `MavixWeb/`) как dir-builds.

### 9.2. Подготовка VPS

```sh
# 1. Поставить docker + compose plugin (Ubuntu 24.04)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 2. Открыть порты на firewall (если ufw)
sudo ufw allow 8000/tcp     # MavixServer
sudo ufw allow 3001/tcp     # MavixWeb
sudo ufw allow 3478/tcp     # coturn
sudo ufw allow 3478/udp
sudo ufw allow 5349/tcp     # turns (если включишь TLS на coturn)
sudo ufw allow 5349/udp
sudo ufw allow 49152:65535/udp  # coturn relay range
# когда поднимешь Caddy:
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 9.3. Деплой

```sh
# 1. Подготовить директорию
mkdir -p /srv/mavix && cd /srv/mavix

# 2. Склонить репозитории (нужен PAT - см. раздел "git клонирование" в README)
git clone https://github.com/AurunChill/MavixServer
git clone https://github.com/dexstronggg/MavixWeb

# 3. Положить docker-compose.yaml, .env.example, Caddyfile из локалки
#    (rsync с твоей машины) или создать их по содержимому из этой репы:
rsync -av ~/Projects/Mavix/{docker-compose.yaml,.env.example,Caddyfile} \
          user@<vps-ip>:/srv/mavix/

# 4. Подготовить .env-ы
cd /srv/mavix
cp .env.example .env                                # POSTGRES_*
cp MavixServer/.env.example MavixServer/.env        # JWT, SMTP, BUILDS_*
cp MavixWeb/.env.example MavixWeb/.env              # PORT, API_BASE_URL

# 5. ВАЖНО: проверить и поправить URL под публичный IP/домен
# MavixServer/.env:
#   BUILDS_SIGNAL_SERVER_URL=http://<vps-ip>:8000   # или https://<domain>
#   WEB_BASE_URL=http://<vps-ip>:3001               # или https://<domain>
#   CORS_ALLOW_ORIGINS=http://<vps-ip>:3001         # или https://<domain>
#   JWT_SECRET=<32+ случайных символов>             # OBLIGATORY!
#   EMAIL_SMTP_PASSWORD=...                          # app password
# MavixWeb/.env:
#   API_BASE_URL=http://<vps-ip>:8000               # или https://<domain>

# 6. Собрать wheels для MavixBoard (нужен MavixBoard/ рядом)
git clone https://github.com/AurunChill/MavixBoard
cd MavixServer && ./scripts/build_wheels.sh ../MavixBoard && cd ..

# 7. Положить prebuilt desktop (если уже собраны)
#    Linux-бинарь — собирается на твоей машине (./scripts/build_binary.sh).
#    Windows .exe — присылает человек с Windows.
#    Оба кладутся в MavixServer/prebuilt/.

# 8. Поднять
docker compose up --build -d
docker compose ps
curl http://localhost:8000/api/v1/health   # {"status":"ok"}
curl http://localhost:3001/                # HTML лендинга
```

### 9.4. Coturn

Coturn держится **отдельно**, не в этом compose, потому что
использует host networking (диапазон 49152–65535 пробрасывать
маппингом — путь в ад). См. репозиторий coturn-сервера с
`turnserver.conf` и собственным `docker-compose.yaml` (этот файл
лежит у тебя в `/root/stun_turn_server/` на VPS).

Если coturn запущен на той же VPS, что и MavixServer — `STUN_SERVER`
и `TURN_SERVER` в `MavixServer/.env` ссылаются на тот же IP, что
снаружи использует app. Это нормально, никакого NAT-loopback не требуется.

### 9.5. TLS через Caddy

Caddy получает Let's Encrypt-сертификат автоматически, **если домен
резолвится в IP этой VPS**.

1. Дождаться, пока `host drone-mavix.ru` возвращает IP сервера.
2. В `/srv/mavix/docker-compose.yaml` раскомментировать сервис `caddy`
   и его volumes (`caddy_data`, `caddy_config`).
3. В `MavixServer/.env` и `MavixWeb/.env` поменять URL'ы на `https://drone-mavix.ru`.
4. **Убрать публичные порты `8000` и `3001`** у сервисов `app`/`web` —
   Caddy будет ходить к ним через docker-network. Закрыть их на firewall.
5. `docker compose up -d`.

Через минуту-две (Caddy дёрнет HTTP-01 challenge на 80 порту)
сертификат подтянется и `https://drone-mavix.ru` начнёт работать.

### 9.6. Обновление прода

| Что обновилось              | Что делать на VPS                                   |
|-----------------------------|------------------------------------------------------|
| Код MavixServer             | `cd /srv/mavix/MavixServer && git pull && cd .. && docker compose up --build -d app migrator` |
| Код MavixWeb                | `cd MavixWeb && git pull && cd .. && docker compose up --build -d web` |
| `.env` (любой)              | `docker compose restart app` (или `web`)             |
| Wheels MavixBoard           | пересобрать на VPS (`./scripts/build_wheels.sh ../MavixBoard`), `docker compose restart app` (кэш `.tar.gz` инвалидируется автоматически) |
| Desktop бинари              | положить в `MavixServer/prebuilt/`, `docker compose restart app` |
| Caddyfile                   | `docker compose restart caddy`                       |

---

## 10. Типичные грабли

| Симптом                                                          | Причина / лечение                                  |
|------------------------------------------------------------------|----------------------------------------------------|
| Дрон логирует `No address associated with hostname`              | `BUILDS_SIGNAL_SERVER_URL` в `MavixServer/.env` указывает на несуществующий хост (например, дефолт `https://server.example.com`). Поправить, `docker compose restart app`, скачать `.deb` заново. |
| `Сборка для платы временно недоступна` на сайте                  | Нет `wheels/board/*.whl`. Запусти `./scripts/build_wheels.sh ../MavixBoard`. |
| `Сборка ещё не загружена на сервер` для desktop                  | Нет файла в `MavixServer/prebuilt/`. Собери и положи. |
| Подвисший `apt install` mavixdesktop / mavixboard (старая версия) | Это старый `.deb`-инсталлятор. Удалить кэш, удалить старый пакет (`sudo apt remove mavixboard mavixdesktop`), скачать **актуальный** `.tar.gz` или AppImage. |
| `docker compose build` ругается на `dpkg-dev`                    | Старый Dockerfile. Pull актуальную версию репы. |
| Билд бинаря падает на `Hidden import` от PySide6                 | Добавить в `mavixdesktop.spec` в `hiddenimports`. |
| Desktop не видит сервер после обновления адреса                  | Юзер либо перелогинивается, либо открывает Settings (шестерёнка) и правит `SIGNAL_URL` — потом нажимает «Сохранить». |
| Удалил дрон, а MavixBoard на RPi всё ещё работает                 | Это нормально: на RPi процесс продолжит крутиться, но получит 401 при следующем тике и встанет в ретрай. Перезапусти процесс на RPi или удали бинарь — записи в БД он сам не восстановит. Чтобы вернуть дрон в список, надо **заново скачать `.tar.gz`** на сайте. |












<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>
равильнее так:

На RPi4 (он у тебя aarch64 — нужны wheels именно под эту архитектуру):


# 1. Зависимости (один раз)
sudo apt update && sudo apt install -y git python3 python3-pip python3-venv

# 2. Склонить ОБА репа — для wheels нужны и MavixBoard (исходник),
#    и MavixServer (там скрипт build_wheels.sh)
git clone https://github.com/AurunChill/MavixBoard
git clone https://github.com/AurunChill/MavixServer

# 3. Собрать wheels (~5-15 минут на RPi)
cd MavixServer
./scripts/build_wheels.sh ../MavixBoard
ls wheels/board/   # *.whl на ~15 МБ суммарно
Передать на VPS:


# с RPi
scp -r wheels/board/* root@85.198.102.188:/srv/mavix/MavixServer/wheels/board/
На VPS — ничего перезапускать не надо. Кэш .tar.gz инвалидируется автоматически: следующее скачивание увидит, что хеш wheels изменился, и пересоберёт.

.env на RPi для этого шага не нужен — .env нужен только если ты хочешь запустить board из исходников для отладки. Для сборки wheels — нет.

Хорошо, как сбилдить AppImage для mavixdesktop?
На твоей Linux-машине (x86_64):


cd ~/Projects/Mavix/MavixDesktop-UI
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pyinstaller
./scripts/build_binary.sh
Результат: dist/mavixdesktop-linux (~150 МБ).

Отправка на сервер:


scp dist/mavixdesktop-linux root@85.198.102.188:/srv/mavix/MavixServer/prebuilt/
ssh root@85.198.102.188 'cd /srv/mavix && docker compose restart app'
После этого кнопка «Linux (.AppImage)» на сайте отдаёт его как mavixdesktop-linux.AppImage.

Заметки:

venv нужен один раз; следующие билды — просто source .venv/bin/activate && ./scripts/build_binary.sh.
Если pip ругается на отсутствие dev-пакетов (e.g. qt6-base-dev, libgl1) — sudo apt install libgl1 libegl1 libxkbcommon0.
Бинарь зависит от glibc хоста сборки. Безопаснее билдить на относительно старом Linux (Ubuntu 22.04/24.04 норм).
И как на .exe
Сам не соберёшь — нужна Windows-машина. Отдай этому человеку 4 команды:


git clone https://github.com/dexstronggg/MavixDesktop-UI
cd MavixDesktop-UI
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -e . ; pip install pyinstaller ; pyinstaller mavixdesktop.spec
Результат: dist\mavixdesktop.exe. Пусть пришлёт.

Что ему нужно перед этим:

Python 3.12 с https://python.org (галка «Add Python to PATH» при установке).
Если pip ругнётся на «Microsoft Visual C++ 14.0 required» — поставить Microsoft C++ Build Tools с https://visualstudio.microsoft.com/visual-cpp-build-tools/ (включить «Desktop development with C++»).
Доступ к репозиторию (приватный) — твой PAT или добавить его в коллабораторы.
У тебя дальше:


scp mavixdesktop.exe root@85.198.102.188:/srv/mavix/MavixServer/prebuilt/
ssh root@85.198.102.188 'cd /srv/mavix && docker compose restart app'
Кнопка «Windows (.exe)» на сайте начнёт его отдавать.