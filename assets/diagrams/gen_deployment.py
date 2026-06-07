#!/usr/bin/env python3
"""UML Deployment — узлы развёртывания системы Mavix (3D-узлы, артефакты)."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1600, 1040)

# Узел: ПК администратора
c.node3d(70, 170, 250, 130, 'ПК администратора', 'device')
c.artifact(92, 225, 206, 65, 'Браузер', 'MavixWeb UI', stereo='execution env')

# Узел: Сервер VPS (Docker)
c.node3d(500, 130, 480, 270, 'Сервер VPS', 'device')
c.text(740, 178, '«executionEnvironment» Docker Compose', fs=11, italic=True)
c.artifact(520, 195, 140, 145, 'MavixServer', '[FastAPI]')
c.artifact(672, 195, 130, 145, 'MavixWeb', '[Express]')
c.artifact(816, 195, 144, 145, 'PostgreSQL', '[СУБД]')

# Узел: ПК оператора
c.node3d(1110, 150, 370, 360, 'ПК оператора', 'device')
c.artifact(1132, 205, 326, 85, 'MavixDesktop', '[PySide6, aiortc]')
c.artifact(1132, 300, 326, 75, 'QGroundControl', 'MAVLink-полёт')
c.artifact(1132, 395, 326, 60, 'Джойстик', 'USB', stereo='device')

# Узел: Дрон (Raspberry Pi)
c.node3d(500, 690, 480, 280, 'Дрон — Raspberry Pi (Ubuntu)', 'device')
c.artifact(520, 748, 250, 100, 'MavixBoard', '[GStreamer, Python]')
c.artifact(800, 748, 160, 100, 'Полётный контр.', 'PX4 / Betaflight', stereo='device')
c.artifact(520, 868, 250, 70, 'Камеры', 'USB / CSI', stereo='device')

# --- communication paths (сплошные линии, стереотип протокола вбок) -----------
# Браузер — VPS
c.poly([(320, 250), (500, 250)], marker='arr')
c.text(410, 240, '«HTTPS»', fs=12)
# ПК оператора — VPS
c.poly([(1110, 250), (996, 250)], marker='arr')
c.text(1053, 240, '«HTTPS / WSS»', fs=12)
# Дрон — VPS (вверх; левее заголовка)
c.poly([(560, 748), (560, 400)], marker='arr')
c.text(572, 560, '«WSS» сигналинг + enrollment', fs=12, anchor='start')
# ПК оператора — Дрон (WebRTC, двунаправленно)
c.poly([(1250, 510), (1250, 820), (996, 820)], marker='arr')
c.poly([(996, 800), (1230, 800), (1230, 510)], marker='arr')
c.text(1245, 660, '«WebRTC»', fs=12, anchor='start')
c.text(1245, 678, 'видео + data', fs=12, anchor='start')
# MavixBoard — FC
c.poly([(770, 798), (800, 798)], marker='arr')
c.text(785, 788, '«UART»', fs=11)
# MavixBoard — Камеры
c.poly([(645, 848), (645, 868)], marker='arr')
c.text(657, 862, '«USB/CSI»', fs=11, anchor='start')

out = pathlib.Path(__file__).parent / 'deployment.svg'
out.write_text(c.svg('Рисунок 6 – Диаграмма развёртывания (Deployment) системы Mavix'), encoding='utf-8')
print(out)
