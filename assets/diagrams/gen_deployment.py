#!/usr/bin/env python3
"""UML Deployment — узлы развёртывания системы Mavix."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1560, 1020)


def node(x, y, w, h, title):
    c.rect(x, y, w, h, sw=1.6)
    c.text(x + w / 2, y + 26, title, fs=16, bold=True)


# Узел: ПК администратора
node(70, 150, 300, 150, 'ПК администратора')
c.box(95, 205, 250, 75, 'Браузер', '(MavixWeb UI)', sw=1.1, title_fs=15)

# Узел: VPS (Docker)
node(500, 110, 480, 280, 'Сервер VPS — Docker Compose')
c.box_multi(520, 170, 140, 150, ['MavixServer', '[FastAPI]', 'REST·WS'], sw=1.1)
c.box_multi(675, 170, 130, 150, ['MavixWeb', '[Express]', 'статика'], sw=1.1)
c.box_multi(820, 170, 140, 150, ['PostgreSQL', '[СУБД]', 'тома'], sw=1.1)

# Узел: ПК оператора
node(1100, 130, 380, 360, 'ПК оператора')
c.box(1125, 185, 330, 90, 'MavixDesktop', '[PySide6, aiortc]', sw=1.1, title_fs=16)
c.box(1125, 295, 330, 80, 'QGroundControl', '(MAVLink-полёт)', sw=1.1, title_fs=15)
c.box(1125, 395, 330, 70, 'Джойстик (USB)', None, sw=1.1, title_fs=15)

# Узел: Дрон (Raspberry Pi)
node(500, 650, 480, 290, 'Дрон — Raspberry Pi (Ubuntu)')
c.box_multi(520, 705, 250, 100, ['MavixBoard', '[GStreamer, Python]', 'WebRTC-борт'], sw=1.1)
c.box_multi(800, 705, 160, 100, ['Полётный', 'контроллер', 'PX4 / Betaflight'], sw=1.1)
c.box(520, 825, 250, 80, 'Камеры', 'USB / CSI', sw=1.1, title_fs=15)

# --- связи (протоколы на рёбрах) ----------------------------------------------
# Браузер -> VPS
c.poly([(370, 242), (500, 242)], marker='arr')
c.text(435, 232, 'HTTPS', fs=13)
# ПК оператора -> VPS
c.poly([(1100, 230), (980, 230)], marker='arr')
c.text(1040, 220, 'HTTPS + WSS', fs=13)
# Дрон -> VPS (вверх; левее заголовка узла, чтобы не пересекать текст)
c.poly([(560, 705), (560, 390)], marker='arr')
c.text(572, 540, 'WSS-сигналинг + enrollment', fs=13, anchor='start')
# ПК оператора <-> Дрон: WebRTC P2P
c.poly([(1250, 490), (1250, 790), (980, 790)], marker='arr')
c.poly([(980, 770), (1230, 770), (1230, 490)], marker='arr')
c.text(1245, 700, 'WebRTC P2P', fs=13, anchor='start')
c.text(1245, 718, '(видео + data)', fs=13, anchor='start')
# MavixBoard -> ПК (через STUN/TURN) уже показано WebRTC
# MavixBoard -> FC (UART)
c.poly([(770, 755), (800, 755)], marker='arr')
c.text(785, 745, 'UART', fs=12)
# MavixBoard -> Камеры
c.poly([(645, 805), (645, 825)], marker='arr')
c.text(657, 820, 'USB/CSI', fs=12, anchor='start')

out = pathlib.Path(__file__).parent / 'deployment.svg'
out.write_text(c.svg('Рисунок 6 – Диаграмма развёртывания (Deployment) системы Mavix'), encoding='utf-8')
print(out)
