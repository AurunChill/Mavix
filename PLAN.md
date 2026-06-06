# PLAN.md — Переход Mavix: дистанционное управление → автоматизированная доставка грузов

> Документ описывает **что** и **как** мы делаем при переделке эталонного проекта
> Mavix (FPV-управление дроном) в **автоматизированную систему доставки
> малогабаритных грузов**. Работаем по gitflow, соблюдаем SOLID / DRY / KISS / YAGNI.
> Эталонная версия замораживается в ветке `remote_control`, вся новая разработка —
> в `delivery_control`.

Дата составления: 2026-06-06.

---

## 1. Контекст и цель

Текущая система — три участника, связанные через сервер:

- **MavixBoard** (Raspberry Pi на дроне) — стримит видео по WebRTC, принимает RC-команды.
- **MavixDesktop-UI** (PC) — оператор смотрит видео, рулит джойстиком.
- **MavixServer + MavixWeb** — сигнальный сервер (WebRTC signaling, auth, раздача сборок) и веб (лендинг + ЛК).

Цель переделки — превратить это в систему **доставки грузов** по модели «как в такси»:
администратор формирует заявки на доставку, операторы их принимают и выполняют ручным
пилотированием, груз сбрасывается в точке назначения, всё логируется.

Новые роли:

| Роль | Кто | Через что входит | Регистрация |
|---|---|---|---|
| **Администратор** | Владелец дронов, диспетчер | MavixWeb (админ-панель) | сам регистрируется/логинится (как сейчас) |
| **Оператор** | Пилот | MavixDesktop-UI | создаётся администратором, креды генерируются |
| **Дрон (board)** | Устройство | — | саморегистрация при первом запуске |

---

## 2. Новая архитектура и поток доставки

```
        ┌──────────────────────────── MavixServer ────────────────────────────┐
        │  REST: auth(admin/operator) · operators · deliveries · drones        │
        │  enroll(board) · builds · ice-servers                                │
        │  WS:  /ws/drone  /ws/gcs(operator)  /ws/admin                        │
        │  DB:  users(admins) · operators · operator_drones · drones · deliveries│
        └───▲─────────────────▲───────────────────▲──────────────────▲────────┘
            │ REST/WS          │ enroll+WS         │ REST/WS          │ WebRTC signaling
            │                  │                   │                  │
   ┌────────┴────────┐   ┌─────┴──────┐    ┌────────┴────────┐        │
   │  MavixWeb       │   │ MavixBoard │    │ MavixDesktop-UI │        │
   │  (админ-панель) │   │  (дрон)    │    │   (оператор)    │◄───────┘
   └─────────────────┘   └─────┬──────┘    └────────┬────────┘
                               │   WebRTC: video + telemetry + control + drop
                               └────────────────────┘
```

**Сценарий доставки (happy path):**

1. Админ регистрируется/логинится в MavixWeb.
2. Админ скачивает **один** board-`tar.gz` (в нём только `USER_ID` + `ENROLLMENT_TOKEN`, без `DRONE_ID`).
3. Ставит ПО на N своих дронов. Каждый дрон при **первом запуске** сам генерирует
   `DRONE_ID`, получает имя, регистрируется на сервере и привязывается к админу.
4. Админ создаёт оператора (ФИО, город, …) → система генерирует `username`+`password`.
   (Дроны за операторами не закрепляются — заявку видят все операторы админа.)
5. Админ отправляет оператору ссылку на скачивание desktop (публичная страница) и креды.
6. Админ создаёт **заявку на доставку** (дрон + адрес/координаты + опц. описание груза).
7. Заявка как «заказ такси» рассылается подходящим операторам в desktop → **кто первый
   принял, тот и выполняет**.
8. Оператору открывается экран управления дроном (видео + джойстик + карта в углу).
9. Долетев, оператор жмёт «**Сброс груза**» → дрон сбрасывает груз → доставка помечается
   `delivered` → админ получает уведомление.
10. Все доставки и их статусы видны админу в журнале.

---

## 3. Принципы разработки

- **SOLID.** Каждый новый слой — единственная ответственность: модели (ORM) ↔
  репозитории (доступ к БД) ↔ сервисы (бизнес-логика) ↔ api/ws (транспорт). Жизненный
  цикл доставки — отдельный сервис `DeliveryService` (state machine), не размазан по
  хендлерам. Аутентификация админа и оператора — через общий контракт, разные реализации.
- **DRY.** Компонент карты (Leaflet + leaflet-rotate) пишем **один раз** как статический
  JS-asset и переиспользуем в MavixWeb и в MavixDesktop (через `QWebEngineView`). CRSF/
  MAVLink-парсинг GPS уже есть в board — расширяем, не дублируем. REST-клиент в web (`api.js`)
  расширяем, не плодим новый.
- **KISS.** Сброс груза — это просто выделенный AUX RC-канал (FC уже умеет рулить серво по
  каналу) + бизнес-событие; не изобретаем новый бортовой протокол. Уведомления — поверх уже
  существующей WS-инфраструктуры, без брокера сообщений.
- **YAGNI.** Не делаем: автопилот/маршрутизацию, оплату, мобильное приложение, мультиарендность
  сверх «админ → его операторы/дроны». Live-трекинг дрона на карте у админа — только если
  дёшево ляжет на уже передаваемую телеметрию (иначе во вторую очередь, см. §10).

---

## 4. Git-стратегия (gitflow)

Репозитории независимы (свои origin), дефолтные ветки разные:

| Репозиторий | origin | Текущая ветка |
|---|---|---|
| Mavix (родитель) | AurunChill/Mavix | `master` |
| MavixServer | AurunChill/MavixServer | `master` |
| MavixBoard | AurunChill/MavixBoard | `main` |
| MavixWeb | dexstronggg/MavixWeb | `main` |
| MavixDesktop-UI | dexstronggg/MavixDesktop-UI | `main` |

**Модель веток (в каждом из 5 репозиториев):**

- `remote_control` — **замороженный эталон** (снимок текущего состояния, тема «дист. управление»).
- `delivery_control` — **интеграционная ветка** новой темы (роль gitflow `develop`/`main`).
- `feature/*` — ветки под конкретные задачи, ответвляются от `delivery_control`, вливаются
  обратно через `--no-ff` merge (или PR). Пример: `feature/server-operators`,
  `feature/board-self-enroll`, `feature/desktop-map`, `feature/web-admin-panel`.
- Релизные метки — тег `delivery-v0.1` на стабильных срезах `delivery_control`.

**Команды установки веток (Phase 0, выполняется в каждом репо):**

Решение (см. §10-Г): **копия без переименования** — `main`/`master` не трогаем, дефолтная
ветка на origin не меняется.

```sh
git branch remote_control                   # копия текущего состояния = эталон
git switch -c delivery_control              # новая ветка разработки от текущего HEAD
# публикация — новые ветки, аддитивно, дефолтную не меняет:
git push -u origin remote_control
git push -u origin delivery_control
```

> Родительский репозиторий Mavix содержит 4 компонента как вложенные git-репозитории
> (gitlink без `.gitmodules`). Ветки заводим и в нём, и в каждом компоненте; PLAN.md
> коммитим в `delivery_control` родителя.

**Правила коммитов:** Conventional Commits (как уже принято в репах: `feat(...)`,
`refactor(...)`, `docs(...)`), на русском. Каждая feature-ветка — атомарна и проходит
`ruff`/`mypy`/тесты перед merge.

> ⚠️ Переименование дефолтной ветки и push в общий origin — действие, меняющее
> состояние удалённого репозитория. Phase 0 выполняем **только после подтверждения**
> (см. §10, вопрос Г).

---

## 5. Модель данных (MavixServer, PostgreSQL + Alembic)

Существующее: `users` (станут **администраторами**), `drones`.

### Изменения существующих таблиц

`users` (= администраторы):
- `+ enrollment_token VARCHAR(64) UNIQUE NOT NULL` — секрет провижининга дронов, вшивается
  в board-tarball. Генерируется при регистрации, ротируемый (можно добавить endpoint позже — YAGNI).
- (роль не вводим отдельной колонкой: web-логин = только админ; оператор живёт в своей таблице.)

`drones`:
- `+ name VARCHAR(64)` — человекочитаемое имя из двух слов (генерится сервером).
- `+ enrolled_at TIMESTAMPTZ NULL` — момент саморегистрации.
- `drone_token` остаётся (выдаётся при enroll, используется для `/ws/drone`).

### Новые таблицы

`operators`:
| Поле | Тип | Назначение |
|---|---|---|
| `operator_id` | VARCHAR(32) PK | id оператора |
| `admin_id` | VARCHAR(32) FK→users | владелец-администратор |
| `username` | VARCHAR(64) UNIQUE | автогенерируемый логин |
| `password` | VARCHAR(256) | bcrypt-хеш автогенерируемого пароля |
| `full_name` | VARCHAR(254) | ФИО |
| `city` | VARCHAR(128) NULL | город |
| `is_active` | BOOL | активен/заблокирован |
| `created_at`/`updated_at` | TIMESTAMPTZ | |

> Закрепление дронов за операторами **не делаем** (решение §10-А): таблицы
> `operator_drones` нет. Оператор принадлежит админу (`admin_id`); заявку видят все
> операторы этого админа.

`deliveries`:
| Поле | Тип | Назначение |
|---|---|---|
| `delivery_id` | VARCHAR(32) PK | |
| `admin_id` | VARCHAR(32) FK→users | кто создал |
| `drone_id` | VARCHAR(64) FK→drones | назначенный дрон |
| `operator_id` | VARCHAR(32) FK→operators NULL | кто принял (до accept — NULL) |
| `status` | VARCHAR(16) | `created`→`offered`→`accepted`→`in_flight`→`delivered` / `cancelled` |
| `dest_address` | VARCHAR(512) NULL | адрес текстом |
| `dest_lat`/`dest_lon` | DOUBLE NULL | координаты (с карты/ввода) |
| `cargo_description` | VARCHAR(512) NULL | **необязательное** (гос. структуры могут не указывать) |
| `created_at`/`offered_at`/`accepted_at`/`delivered_at`/`cancelled_at` | TIMESTAMPTZ NULL | таймлайн |

**Миграции Alembic** (по одной на изменение, в порядке): `add_enrollment_token_to_users`
→ `add_name_enrolled_to_drones` → `create_operators` →
`create_deliveries`. Тесты на SQLite, прод — Postgres (как сейчас).

---

## 6. Ключевые проектные решения

### 6.1 Саморегистрация board (мой ответ на вопрос про эндпоинт)

**Рекомендация: отдельный non-JWT эндпоинт enroll, аутентифицируемый provisioning-токеном.**

Обоснование: JWT — для интерактивных пользователей (короткий access + refresh). Дрон —
headless-устройство, ему нужен **долгоживущий статический секрет**. Это классический IoT-
паттерн device enrollment / group enrollment key (Azure DPS, WSO2): в прошивку вшивается
общий для админа секрет, устройство им подтверждает право зарегистрироваться, сервер выдаёт
устройству его персональный долговременный токен.

> Только `USER_ID` вшивать **небезопасно**: `user_id` не секрет — зная его, кто угодно
> привязал бы чужие дроны к админу. Поэтому в tarball кладём `USER_ID` **и**
> `ENROLLMENT_TOKEN` (секрет админа). Это минимальное безопасное решение и оно остаётся
> простым (KISS): один статический токен, без OAuth-плясок.

Поток:

```
board (первый запуск, в .env нет DRONE_ID):
  drone_id = uuid4().hex                       # 32 hex, генерим локально
  POST /api/v1/drones/enroll
       Authorization: Enroll <ENROLLMENT_TOKEN>
       body: { user_id, drone_id }
server:
  validate ENROLLMENT_TOKEN ↔ users.enrollment_token ↔ user_id
  name = two_words()                           # рандом из 2×~1000 слов
  drone = create_or_get(drone_id, user_id, name, drone_token=gen())   # идемпотентно по drone_id
  → 201 { drone_id, drone_token, name }
board:
  записать DRONE_ID, DRONE_TOKEN, DRONE_NAME в .env (preset.env)
  дальше работать как раньше: /ws/drone с DRONE_TOKEN
```

Идемпотентность: повторный enroll того же `drone_id` тем же админом возвращает существующую
запись (не плодим дубли). Конфликт `drone_id` от другого админа → `409`, board
перегенерирует id. Генерация имени и `drone_token` — на сервере (единый источник, web
сразу видит имя). Перенос регистрации со «скачивания» на «запуск» означает: в `builds`-
сервисе **убираем** предварительное создание дрона; tarball больше не привязан к
конкретному `drone_id`, поэтому **один build на админа** (упрощает кэш).

Файлы: `MavixServer/src/mavixserver/api/drones.py` (+`enroll`),
`services/drone.py`, `services/build.py`, `models/user.py`, `core/security.py` (генерация
токена), новый `services/naming.py` (два-словное имя);
`MavixBoard/src/mavixboard/__main__.py` + `core/config.py` (enroll-at-startup, запись .env);
`MavixServer/build-templates/board/preset.env.template` (плейсхолдеры `USER_ID`,
`ENROLLMENT_TOKEN`, без `DRONE_ID`).

### 6.2 Аутентификация оператора

- Новый эндпоинт `POST /api/v1/auth/operator/login { username, password }` → JWT с
  `sub=operator_id`, claim `role=operator`. Refresh — по аналогии с админским (переиспуем
  `core/security.py`, добавив `role` в payload; декодер возвращает (subject, role)).
- Desktop логинится этими кредами; WS `/ws/gcs` принимает operator-JWT (хендлер проверяет
  `role=operator`, грузит закреплённые дроны).
- Админский `/auth/login` — без изменений (web).
- Операторы **не** регистрируются сами: только `POST /api/v1/operators` (admin-JWT) с
  автогенерацией `username` (напр. `op-<6hex>` или из ФИО) и пароля (выдаётся админу в ответе
  один раз, в БД — только хеш).

### 6.3 Жизненный цикл доставки (state machine, «такси»)

```
created ──(admin создаёт)──> offered ──(operator accept, атомарно)──> accepted
                               │                                          │
                               │ (никто не принял / timeout / admin)      │ (operator подключился к дрону)
                               ▼                                          ▼
                           cancelled                                   in_flight
                                                                          │ (operator: drop груза)
                                                                          ▼
                                                                      delivered
```

- **Создание:** `POST /api/v1/deliveries` (admin-JWT) → статус `offered`. Сервер пушит
  `delivery_offer` **всем онлайн-операторам этого админа** (закрепления дронов нет, §10-А).
- **Приём (гонка как в такси):** `POST /api/v1/deliveries/{id}/accept` (operator-JWT).
  Атомарно: `UPDATE deliveries SET operator_id=?, status='accepted', accepted_at=now()
  WHERE delivery_id=? AND status='offered'`. `rowcount==1` → выиграл; `0` → «уже занято».
  Остальным операторам — `delivery_taken`; админу — `delivery_accepted`.
- **Полёт:** при установлении WebRTC-сессии оператора с дроном → `in_flight`.
- **Доставка:** сброс груза (см. 6.6) → `delivered` + уведомление `delivery_delivered` админу.
- **Отмена:** `POST /api/v1/deliveries/{id}/cancel` (admin) пока не `delivered`.

Вся логика — в `services/delivery.py` (single responsibility), переходы валидируются (нельзя
`delivered` из `offered` и т.п.).

### 6.4 WS-протокол: уведомления

Переиспуем существующую WS-инфраструктуру (heartbeat, throttle, registry):

- `/ws/drone` — без изменений (board, WebRTC signaling).
- `/ws/gcs` — оператор: WebRTC signaling **плюс** новые сообщения доставки:
  `← delivery_offer {delivery_id, drone_id, drone_name, dest, cargo?}`,
  `← delivery_taken {delivery_id}`, `→ accept {delivery_id}` (или через REST + push).
- `/ws/admin` — **новый**: подключение веб-панели админа; сервер шлёт
  `drone_enrolled`, `delivery_accepted`, `delivery_delivered`. Аутентификация — admin-JWT
  (как gcs). Реестр расширяем `_admins: dict[admin_id → sender]`.

`ConnectionRegistry` дополняем индексами `admin_id → ws`, `operator_id → ws`,
`admin_id → {operator_id}` для адресной рассылки.

### 6.5 GPS-телеметрия и вращающаяся карта

**Board → Desktop (телеметрия по выделенному data-channel):** управление уже идёт через
WebRTC, поэтому телеметрию шлём **отдельным data-channel** `telemetry` (а НЕ через
config/packet-канал) — решение §10-В. В board уже парсятся CRSF (GPS `0x02`, ATTITUDE
`0x1E`) и MAVLink (`GLOBAL_POSITION_INT 33`, `VFR_HUD 74`/`ATTITUDE`). Достаём `lat, lon,
alt, heading(yaw)` и шлём ~2–5 Гц JSON `{type:'telemetry', lat, lon, heading, sats, alt}`.
Новый `TelemetryChannel` добавляем рядом с `PacketChannel`/`PingChannel`/`ConfigChannel` в
`webrtc/channels.py` (board и desktop). Парсинг — в существующих `fc/crsf.py`,
`fc/mavlink.py`; агрегирование/throttle — в `fc/service.py` (DRY: дополняем, не переписываем).

Живой трекинг дрона на карте у админа **пока не делаем** (§10-В) — телеметрия ходит только
дрон↔оператор по data-channel, через сервер не ретранслируется.

**Карта (общий компонент, DRY):** Leaflet + плагин
[`Raruto/leaflet-rotate`](https://github.com/Raruto/leaflet-rotate) (`setBearing`/
`getBearing`). Логика «север всегда по носу дрона» = `map.setBearing(-heading)`; маркер
дрона в центре, маркер назначения — из принятой заявки. Пишем один JS-модуль
`map-widget.js` (+ css) и используем:
- **MavixWeb** — `<div>` на странице доставок (выбор точки кликом при создании; просмотр).
- **MavixDesktop** — `QWebEngineView` грузит тот же `map-widget.html`; телеметрия толкается
  в карту через `page.runJavaScript("updateDrone(lat,lon,heading)")`
  ([приём из Qt-сообщества](https://forum.qt.io/topic/161101/how-to-implement-smoothly-updating-map-in-qt-widgets-app)).
  Карта — оверлеем в углу `FlightWindow`.

Тайлы — OpenStreetMap (бесплатно). Оффлайн-кэш тайлов — YAGNI (во вторую очередь).

### 6.6 Сброс груза

Разделяем **физику** и **бизнес-событие** (KISS, разделение ответственности):

- **Физика:** выделенный AUX RC-канал (напр. CH8). FC уже умеет рулить серво/gripper по
  каналу — новый бортовой протокол не нужен. На MAVLink-FC альтернатива —
  `MAV_CMD_DO_SET_SERVO`/`DO_GRIPPER` (если канал недоступен). Кодирование канала — в
  `MavixDesktop/src/mavixdesktop/fc/encoder.py` (+ бит/канал «drop»), приём — в board как
  обычный RC.
- **UI:** в калибровке джойстика (`joystick/` + экран `joystick_setup`) добавляем привязку
  кнопки «Сброс груза» (кнопка пульта или экранная). Нажатие → выставить drop-канал +
  отправить config-событие `{type:'drop_cargo', delivery_id}`.
- **Бизнес-событие:** desktop по WS/REST помечает доставку `delivered` →
  сервер шлёт админу `delivery_delivered`. (Подтверждение факта сброса — по нажатию
  оператора; телеметрию серво-обратной-связи не закладываем — YAGNI.)

---

## 7. Детальный разбор по репозиториям

### 7.1 MavixServer (бэкенд) — пункты 1,3,4,5,7,8

1. Модели + миграции: `enrollment_token` в users; `name`,`enrolled_at` в drones; новые
   `operators`, `operator_drones`, `deliveries` (§5).
2. `core/security.py`: генерация enrollment-токена; operator-JWT (`role` в payload),
   декодер с ролью. `services/naming.py`: два-словное имя (списки `~1000` прил. + `~1000`
   сущ., можно «смешные»).
3. `api/drones.py`: `POST /drones/enroll` (non-JWT, Enroll-токен, §6.1); существующая
   регистрация при скачивании — убрать.
4. `api/operators.py` (новый): CRUD операторов (admin-JWT), автогенерация креды.
   `repositories/operator.py`, `services/operator.py`. (Закрепление дронов за операторами
   не делаем, §10-А.)
5. `api/auth.py`: `+ /auth/operator/login`.
6. `api/deliveries.py` (новый): `POST /deliveries`, `GET /deliveries` (журнал админа),
   `POST /deliveries/{id}/accept` (operator), `/cancel`, `/delivered`.
   `services/delivery.py` (state machine, §6.3), `repositories/delivery.py`.
7. `ws/`: новый `/ws/admin` + admin_handler; в `gcs_handler` — сообщения доставки;
   `registry.py` — индексы admin/operator; рассылки в `relay.py`/новом `notifier.py`.
8. `services/build.py`: tarball без предрегистрации дрона, плейсхолдеры `USER_ID`+
   `ENROLLMENT_TOKEN`; **убрать desktop из авторизованной раздачи** (desktop станет
   публичным, см. web). Board-сборка — один артефакт на админа.
9. Тесты под всё новое (REST + WS + services), SQLite.

### 7.2 MavixWeb (админ-панель) — пункты 1,4,8,10

1. Позиционирование: сайт = **админ-портал** (регистрация/логин как есть). Лендинг —
   переписать под доставку (§ пункт 10).
2. Новые страницы ЛК: **Операторы** (список, создание с показом сгенерированных креды один
   раз), **Дроны** (список саморегистрированных, имя/статус/онлайн), **Доставки** (создание
   с картой выбора точки + журнал статусов, §8), **Доставлено/уведомления** (WS `/ws/admin`
   → тосты `drone_enrolled`/`delivery_delivered`). Карта у админа — только выбор/просмотр
   точки назначения, без живого трекинга дрона (§10-В).
3. **Скачивания:** board-`tar.gz` — только в админском ЛК. **Desktop — убрать с
   авторизованной страницы**; сделать **публичную** страницу `/download/desktop` (без
   регистрации) для операторов.
4. `js/api.js` — добавить методы (operators, deliveries, enroll-не нужен). `js/map-widget.js`
   — общий компонент карты (§6.5). WS-клиент для админ-уведомлений.
5. Ребрендинг текста/иконок: «дистанционное управление» → «доставка грузов» (пункт 10).
6. Тесты Jest на новые роуты/страницы.

### 7.3 MavixBoard (дрон) — пункты 2,3,7,9

1. `__main__.py` + `core/config.py`: enroll-at-startup (§6.1) — если в `preset.env` нет
   `DRONE_ID`, сгенерировать, вызвать `/drones/enroll`, дописать `DRONE_ID/DRONE_TOKEN/
   DRONE_NAME` в `.env`; иначе пропустить. Идемпотентно при рестартах.
2. Телеметрия GPS+heading: расширить `fc/crsf.py`/`fc/mavlink.py` декодерами, агрегировать в
   `fc/service.py`, слать по data-channel (§6.5).
3. Сброс груза: принимать config-событие `drop_cargo` и/или AUX-канал; на MAVLink — опц.
   `DO_SET_SERVO` (§6.6).
4. Тесты на enroll-логику (mock REST), парсинг GPS/heading.

### 7.4 MavixDesktop-UI (оператор) — пункты 4,6,7,9

1. Логин оператора (`/auth/operator/login`), хранение токена (keyring) — переиспуем `server/`.
2. **Убрать экран списка дронов** (`screens/drone_list_page.py`); дрон берётся из принятой
   заявки/назначения. Навигация: Login → (ожидание заявок) → принятие → FlightWindow.
3. **Перенести настройки** в **кнопку** на экране управления (`screens/drone_view`/
   `flight_window`) вместо отдельной страницы списка.
4. **Уведомление-заявка** (`delivery_offer`) с кнопкой «Принять» (модал/тост); accept →
   REST/WS; «занято» — закрыть.
5. **Карта** в углу FlightWindow: `QWebEngineView` + общий `map-widget` (§6.5),
   обновление по телеметрии.
6. **Кнопка «Сброс груза»** в калибровке джойстика + drop-канал в `fc/encoder.py` +
   пометка доставки `delivered` (§6.6).
7. Ребрендинг UI под доставку. Тесты (pytest-qt, mock coordinator).

---

## 8. Фазы и порядок работ (зависимости)

Сервер — фундамент, поэтому впереди. Внутри фаз — feature-ветки от `delivery_control`.

- **Phase 0 — git-инфраструктура.** Ветки `remote_control`/`delivery_control` во всех репо
  (§4). *Блокирует всё.*
- **Phase 1 — Server: данные и auth.** Миграции (operators/operator_drones/deliveries,
  enrollment_token, drone.name), operator-JWT, CRUD операторов + назначение дронов.
- **Phase 2 — Server: enroll + builds.** `/drones/enroll`, генерация имени, перестройка
  builds (USER_ID+ENROLLMENT_TOKEN, один артефакт; desktop → публичный).
- **Phase 3 — Board: саморегистрация.** Enroll-at-startup + запись .env. *Зависит от Phase 2.*
- **Phase 4 — Server: доставки + WS.** `DeliveryService` (state machine), эндпоинты,
  `/ws/admin`, уведомления, рассылка offer/accept (такси-гонка).
- **Phase 5 — Web: админ-панель.** Операторы, дроны, доставки (+карта выбора точки), журнал,
  WS-уведомления, разделение скачиваний, ребрендинг.
- **Phase 6 — Desktop: оператор.** Логин оператора, убрать список дронов, настройки-кнопка,
  уведомления-заявки, accept. *Зависит от Phase 4.*
- **Phase 7 — Телеметрия + карта.** Board GPS/heading по data-channel; общий map-widget;
  карта в desktop (вращение) и web. *Зависит от Phase 3, 6.*
- **Phase 8 — Сброс груза.** UI-кнопка + drop-канал (board/desktop) + статус `delivered` +
  уведомление админу. *Зависит от Phase 4, 6.*
- **Phase 9 — Ребрендинг/доки/тесты.** Привести USER_GUIDE/TECHNICAL/README под доставку,
  прогнать `ruff`/`mypy`/pytest/jest, обновить `BUILD.md`/`ForServer`.

---

## 9. Тестирование и качество

- Python (Server/Board/Desktop): `pytest` (asyncio_mode=auto), `ruff check`, `mypy --strict`
  — чисто перед каждым merge в `delivery_control`. Стиль кода — по проектному стайл-гайду
  (одинарные кавычки, `from __future__ import annotations`, `%`-логи с тегами `[...]`,
  баннеры-секции и т.д.).
- Web: `jest` (роуты, новые страницы, индикаторы).
- Критичные сценарии с тестами: enroll (идемпотентность, неверный токен), такси-accept
  (гонка → ровно один победитель), state-machine переходы, рассылка по WS нужным операторам.
- Ручная проверка интеграции через `ForServer/Main` docker-compose (db+app+web+caddy).

---

## 10. Решения (подтверждены 2026-06-06) и остаточные вопросы

**А. Кому рассылать заявку — РЕШЕНО.** Закрепление дронов за операторами **не делаем**.
Заявку видят **все операторы, закреплённые за администратором** (по `admin_id`). Таблицу
`operator_drones` и эндпоинт назначения убрали.

**Б. Безопасность enroll — РЕШЕНО.** В tarball вшиваем `USER_ID` + `ENROLLMENT_TOKEN`
(см. §6.1).

**В. Телеметрия и трекинг — РЕШЕНО.** Телеметрия (GPS/heading) ходит **по выделенному
data-channel** дрон↔оператор поверх WebRTC (см. §6.5), не через config-канал и не через
сервер. Живой трекинг дрона на карте у админа **пока не делаем**.

**Г. Git Phase 0 — РЕШЕНО.** Делаем `remote_control` **копией** текущей ветки **без
переименования** `main`/`master`; `delivery_control` — новая ветка разработки (см. §4).

**Д. Карта в desktop.** Выбран `QWebEngineView`+Leaflet (общий компонент с web, DRY) вместо
нативного `QtLocation`. Требует `PySide6-WebEngine` в зависимостях/сборке PyInstaller —
учтём в `.spec`.

---

## 11. Маппинг «пункт ТЗ → задачи»

| Пункт | Где делаем | Раздел |
|---|---|---|
| 1. Админ-панель, сайт для админов | Web, Server(auth) | 7.1, 7.2 |
| 2. Админ качает board tar.gz | Server(builds), Web | 7.1.8, 7.2.3 |
| 3. Board регистрируется при запуске | Server(enroll), Board | 6.1, 7.1.3, 7.3.1 |
| 4. Операторы (создание, креды), публичный desktop | Server(operators), Web, Desktop | 6.2, 7.x |
| 5. Заявка на доставку «как такси» | Server(deliveries+WS), Desktop, Web | 6.3, 6.4 |
| 6. Экран управления, убрать список дронов, настройки-кнопка | Desktop | 7.4.2–3 |
| 7. Сброс груза + уведомление админу | Desktop, Board, Server | 6.6, 7.x |
| 8. Журнал грузов/статусов, описание опционально | Server, Web | 5, 7.1.6, 7.2.2 |
| 9. Карта в углу + GPS-телеметрия + вращение | Board, Desktop, Web | 6.5, 7.x |
| 10. UI web под доставку | Web | 7.2.5 |

---

*Конец плана. После подтверждения вопросов §10 начинаем с Phase 0 (git) → Phase 1 (server).*
