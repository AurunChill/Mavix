# Разбор: почему не поднималось WebRTC-соединение через TURN (и как починили)

Дата: 2026-05-28

## Симптом

Дрон (MavixBoard, GStreamer/`webrtcbin`) ↔ оператор (MavixDesktop-UI, aiortc) не
соединялись, когда обе стороны были за NAT и должны были идти через TURN. В логах:

```
ICE connection state -> checking
ICE connection state -> failed
```

Локально (обе стороны в одной сети) иногда поднималось напрямую, но через интернет /
relay — стабильно `failed`.

---

## Главная причина (то, что реально чинило)

**Desktop неправильно парсил trickle-ICE-кандидаты, приходящие от дрона.**

Дрон (libnice) шлёт свои кандидаты по одному через сигналинг (trickle). На стороне
desktop в `add_remote_ice` ([MavixDesktop-UI/src/mavixdesktop/webrtc/peer.py](MavixDesktop-UI/src/mavixdesktop/webrtc/peer.py))
из строки кандидата вытаскивался только **тип**, а `ip`/`port`/`foundation`/`priority`
оставались пустыми:

```python
ice = RTCIceCandidate(component=1, foundation='', ip='', port=0, priority=0, ...)
ice.candidate = cand_str        # ← а это aiortc игнорирует
await self._pc.addIceCandidate(ice)
```

aiortc 1.14 строит внутренний aioice-кандидат **из полей объекта**, а НЕ из строки
`.candidate`. Поля пустые → кандидат пустой → aioice его отбрасывал:

```
aioice.ice - Connection(0) Remote candidate "" is not valid: '' does not appear to be an IPv4 or IPv6 address
```

Итог: у desktop **не было ни одного удалённого кандидата** → проверять не с чем → ICE
`failed`. Видео-relay тут ни при чём — соединение умирало на этапе обмена кандидатами.

Баг был внесён в коммите `6f8baf1` («parse trickle candidate type»), который добавил
парсинг только типа.

### Фикс

Парсить всю строку кандидата штатным парсером aiortc:

```python
from aiortc.sdp import candidate_from_sdp
sdp_str = cand_str[len('candidate:'):] if cand_str.startswith('candidate:') else cand_str
ice = candidate_from_sdp(sdp_str)   # заполняет ip/port/foundation/priority/type
ice.sdpMid = sdp_mid
ice.sdpMLineIndex = sdp_mline_index
await self._pc.addIceCandidate(ice)
```

Коммит: `6f57384` (MavixDesktop-UI).

---

## Сопутствующие проблемы, найденные по дороге

### 1. Desktop игнорировал локальный TURN-конфиг

`coordinator.py` всегда брал список ICE-серверов из API сервера
(`/api/v1/ice-servers`) и затирал то, что прописано в `config.py`. Поля
`turn_server`/`stun_server`/… были «мёртвыми» — нигде в WebRTC-пути не читались.

**Фикс:** `_local_ice_servers()` в `coordinator.py` — если локально задан STUN/TURN,
используем его; на сервер идём только если локально пусто.

### 2. force_relay на desktop был «ненастоящим»

aiortc 1.14 не отдаёт `iceTransportPolicy` через `RTCConfiguration`, поэтому
force_relay реализовывался вырезанием не-relay строк из SDP. Но ICE-агент aiortc при
этом всё равно работал в режиме `transport_policy=ALL`, собирал host/srflx и слал
с них проверки. Когда сосед — строго relay-only, эти проверки приходили на TURN с
публичного IP, на который у relay-аллокации соседа нет permission, и coturn их дропал.

**Фикс:** `relay_patch.py` — monkeypatch подменяет aioice-`Connection`, которую
создаёт aiortc, на подкласс с `transport_policy=RELAY` (нативный relay-only). Гейтится
живым `settings.force_relay` + наличием TURN. Исходники библиотеки не трогали.

Коммит: `50da147` (MavixDesktop-UI).

### 3. Board не умел force_relay

У GStreamer-стороны не было аналога. Добавлен флаг `FORCE_RELAY` → в `webrtcbin`
подставляется `ice-transport-policy=relay`.

Файлы: `core/config.py`, `gstreamer/pipeline.py`. Коммит: `8fb00f5` (MavixBoard).

---

## Что НЕ было причиной (важно — на это ушло время, чтобы исключить)

Долго подозревали сервер/сеть. Всё это проверено и **исправно**:

- **Порты relay-диапазона 49152–65535** — открыты (проверка `nc -u` снаружи прошла,
  `ufw` разрешает).
- **coturn relay-to-self (relay↔relay)** — работает: `turnutils_uclient -y` дал
  `40/40, потерь 0` и по UDP/3478, и по TLS/443.
- **TLS/TURNS на 443** — работает (turnutils с `-S` тоже 40/40, ранние
  `SSL internal error` — это болячка самого turnutils при ретраях).
- **ACL coturn** (`allowed-peer-ip`/`denied-peer-ip`) — режим default-allow,
  CreatePermission на приватные IP проходит → не режет.
- **Транспорт TURNS:443 vs TURN:3478** — оба ок на уровне сервера.

Вывод, который сэкономил бы время: **получить relay-кандидат ≠ relay работает**, а
`ICE failed` при наличии relay-кандидата чаще всего означает проблему **обмена/применения
кандидатов**, а не самого TURN.

---

## Как диагностировали (полезные инструменты)

1. **`turnutils_uclient -y -u <user> -w <pass> -p <port> -n 10 <host>`** — встроенный
   в coturn тест relay↔relay. Изолирует сервер от приложения: если `recv ≈ send` —
   сервер исправен, копать в коде. Добавить `-S` для TLS-проверки.

2. **`ICE_DEBUG=1 python3 -m mavixdesktop`** — флаг (добавлен в `core/logger.py`)
   включает DEBUG для `aioice`/`aiortc`: видно каждую аллокацию, кандидата, проверку и
   ответ TURN. Именно он показал `Remote candidate "" is not valid` — финальную улику.

3. **Лог coturn** (`journalctl -u coturn` или `/var/log/turnserver.log`):
   - `peer usage: rp=0, rb=0, sp=N, sb=M` — `sp/rp` = отправлено/принято медиа через
     relay. `rp=0` при `sp>0` = проверки уходят, ответы не возвращаются.
   - `CREATE_PERMISSION ... success` — кому разрешён relay. Отсутствие permission на
     relay соседа (`159.194.214.149`) = проверки соседа будут дропаться.

---

## Диагностические заметки по серверу (на будущее, не критично)

- В `/etc/turnserver.conf` стоит `user-quota=12`, а креды `myuser` общие на всех
  клиентов. При утечке аллокаций (board/desktop не всегда закрывают их при teardown —
  в логах `allocation timeout` / `libnice: alive TURN refreshes`) квота может забиться.
  Стоит поднять `user-quota`/`total-quota` или выдавать временные креды.
- Строка `allowed-peer-ip=<external-ip>` бесполезна (default-allow) — можно убрать.
- Для realtime-видео лучше отдавать клиентам и UDP-TURN (`turn:host:3478`), а не только
  `turns:host:443` (TCP/TLS даёт лишнюю задержку и head-of-line blocking).

---

## Затронутые файлы / коммиты

**MavixDesktop-UI:**
- `src/mavixdesktop/coordinator.py` — `_local_ice_servers()` (приоритет локального конфига)
- `src/mavixdesktop/webrtc/relay_patch.py` — нативный relay-only через aioice
- `src/mavixdesktop/webrtc/peer.py` — **фикс парсинга trickle-кандидатов** (главное)
- `src/mavixdesktop/core/logger.py` — флаг `ICE_DEBUG`
- Коммиты: `50da147`, `6f57384`

**MavixBoard:**
- `src/mavixboard/core/config.py`, `src/mavixboard/gstreamer/pipeline.py` — флаг `FORCE_RELAY`
- Коммит: `8fb00f5`

---

## Что ещё проверить

- [ ] Тест с реальным удалённым пиром (другая сеть/NAT, напр. общага) — сначала **без**
      force_relay (прямой путь + relay как fallback), потом с force_relay.
- [ ] Убедиться, что board/desktop корректно закрывают TURN-аллокации при завершении
      сессии (чтобы не текли на сервере).
