# Принципы проектирования в коде Mavix

Примеры применения SOLID, DRY, KISS, YAGNI на реальном коде проекта (со
ссылками на файлы и символы). Текст пригоден для пояснительной записки ВКР.

---

## SOLID

### S — Single Responsibility (единственная ответственность)

**Пример 1. Слои сервера.** Доступ к данным, бизнес-логика и транспорт
разделены: `repositories/delivery.py` умеет только SQL-запросы,
`services/delivery.py` — только бизнес-правила (статусы, снимки),
`api/deliveries.py` — только HTTP. Замена БД не трогает сервисы, смена правил —
не трогает роутеры.

**Пример 2. WebRTC-слой борта** (`MavixBoard/src/mavixboard/webrtc/`,
`gstreamer/`): `GStreamerPipe` — только пайплайн (start/stop/bitrate),
`WebRTCManager` — жизненный цикл сессии, `PeerSession` — сигналинг
offer/answer/ICE, `DataChannelHub` — data-каналы, `FCService` — связь с
полётником. Каждый класс — одна причина для изменения (см. диаграмму классов
`assets/diagrams/png/class_webrtc.png`).

**Пример 3. Десктоп:** `ui/managers/video.py` (VideoManager) — только приём и
отрисовка кадров; `ui/screens/map_widget.py` (MapWidget) — только карта;
`fc/encoder.py` — только кодирование RC-кадров.

### O — Open/Closed (открыт для расширения, закрыт для изменения)

**Пример 1. Поддержка полётных контроллеров** (`MavixBoard/.../fc/`): `detect.py`
определяет тип FC, `crsf.py` и `mavlink.py` — независимые декодеры за общим
контрактом «вернуть унифицированный dict телеметрии». Добавить новый протокол =
новый модуль-декодер, координатор (`coordinator._on_fc_telemetry`) не меняется.

**Пример 2. Источники тайлов карты** (`map_widget.py`, словарь `_SOURCES`):
добавление спутник/улицы/нового провайдера — запись в словарь, логика рендера и
загрузки тайлов не трогается.

### L — Liskov Substitution (подстановка Барбары Лисков)

**Пример 1.** `MavixDesktop-UI/.../webrtc/relay_patch.py` — подкласс
`aioice.Connection` с `transport_policy=RELAY` подставляется вместо базового
класса там, где aiortc создаёт Connection; остальной код aiortc работает с ним
без изменений (нативный relay-only).

**Пример 2.** `ui/managers/connection.py` и `demo_connection.py` —
взаимозаменяемые менеджеры подключения с одинаковым контрактом: UI работает с
любым (реальная сессия или демо) одинаково.

### I — Interface Segregation (разделение интерфейсов)

**Пример 1. Узкие колбэки координатора** (`MavixDesktop-UI/.../coordinator.py`):
`on_telemetry`, `on_battery_changed`, `on_delivery_offer`,
`on_delivery_accepted`, `on_drone_offline`, … — отдельные необязательные хуки.
Потребитель подписывается только на то, что ему нужно, а не на один «толстый»
интерфейс.

**Пример 2.** `DataChannelHub` (`MavixBoard/.../webrtc/channels.py`) раздаёт
именованные каналы `packet`/`ping`/`config`/`telemetry` по отдельности — клиент
берёт только нужный.

### D — Dependency Inversion (инверсия зависимостей)

**Пример 1. Внедрение зависимостей в координатор борта**
(`MavixBoard/.../coordinator.py`, `SessionCoordinator.__init__`): зависит от
абстракций, переданных снаружи, а не создаёт их сам —
```python
def __init__(self, signal_client: SignalClient,
             pipeline_factory: Callable[[], GStreamerPipe | None],
             fc_service: FCService | None = None,
             watcher: CameraWatcher | None = None,
             camera_source: CameraSource | None = None) -> None:
```
Это упрощает тесты (подставляются заглушки) и замену реализаций.

**Пример 2.** Сервисы сервера принимают `AsyncSession` через DI FastAPI
(`api/dependencies.py`), а не открывают соединение сами. `WebRTCManager`
принимает `send`-callable и `webrtc_elem` извне.

---

## DRY (Don't Repeat Yourself)

- **Единый генератор идентификаторов/токенов** `generate(length)` в
  `MavixServer/.../models/admin.py` переиспользуется для `admin_id`,
  `enrollment_token`, `operator_id`, `drone_token`, `delivery_id`.
- **Единый помощник смены статуса** `_set()` в `services/delivery.py` — все
  переходы (`accept`/`set_in_flight`/`mark_delivered`/`cancel`) идут через одну
  функцию (статус + временная метка), без дублирования.
- **`telemetry_to_args()`** (`map_widget.py`) — единственное место разбора
  telemetry-payload в (lat, lon, heading); используется и картой, и приложением.

## KISS (Keep It Simple, Stupid)

- **Приём заявки «как в такси»** — одним атомарным `UPDATE ... WHERE
  status='offered'` (`repositories/delivery.py::try_accept`), без блокировок и
  очередей: выигрывает тот, у кого `rowcount == 1`.
- **Карта на QPainter** вместо QtWebEngine (`map_widget.py`): растровые тайлы +
  `QPainter`, без встраивания Chromium — проще, легче и не роняет приложение.
- **Сервисы и репозитории — обычные функции модуля**, а не иерархии классов:
  меньше церемоний там, где состояние не нужно.

## YAGNI (You Aren't Gonna Need It)

- **Без преждевременных абстракций**: нет репозиторных интерфейсов/DI-контейнеров
  ради «расширяемости» — простые функции, пока этого достаточно.
- **Удалили лишнее**: карта QtWebEngine роняла приложение, а «защита» декодера
  через приватные методы aiortc была построена на ложной предпосылке — обе
  убраны (поведение приведено к проверенному `remote_control`).
- **Только нужные поля/фичи**: `cargo_description` опционально; денормализованные
  снимки в `deliveries` добавлены ровно для одного требования — журнал должен
  переживать удаление дрона/оператора (FK `SET NULL`).
