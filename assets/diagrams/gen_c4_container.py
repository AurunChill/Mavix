#!/usr/bin/env python3
"""C4 уровень 2 — контейнеры системы Mavix."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1600, 940)

# --- контейнеры ---------------------------------------------------------------
c.box(90, 130, 250, 90, 'Браузер админа', '(внешний)', sw=1.2, title_fs=16)
c.box(90, 330, 280, 120, 'MavixWeb', '[Node.js, Express, JS]', sw=1.2)
c.box_multi(560, 295, 340, 155, [
    'MavixServer', '[Python, FastAPI,', 'SQLAlchemy, Docker]',
    'REST · auth · WS-сигналинг'], sw=1.6)
c.box(560, 560, 320, 100, 'PostgreSQL', '[СУБД]', sw=1.2)
c.box_multi(1130, 130, 320, 145, [
    'MavixDesktop', '[Python, PySide6, aiortc]', 'приложение оператора'], sw=1.2)
c.box_multi(1130, 560, 320, 145, [
    'MavixBoard', '[Python, GStreamer,', 'Raspberry Pi] — борт'], sw=1.2)

# --- связи --------------------------------------------------------------------
# Браузер -> Web
c.poly([(215, 220), (215, 330)], marker='arr')
c.text(225, 285, 'HTTPS', fs=14, anchor='start')
# Web -> Server
c.poly([(370, 390), (560, 390)], marker='arr')
c.text(465, 380, 'REST API (JWT)', fs=14)
# Server -> PostgreSQL
c.poly([(720, 450), (720, 560)], marker='arr')
c.text(732, 510, 'SQL (asyncpg)', fs=13, anchor='start')
# Desktop -> Server (REST + WS)
c.poly([(1180, 275), (1180, 360), (900, 360)], marker='arr')
c.text(1040, 350, 'REST + WS-сигналинг', fs=13)
# Board -> Server (WS + enrollment)
c.poly([(1180, 560), (1180, 405), (900, 405)], marker='arr')
c.text(1040, 422, 'WS-сигналинг + enrollment', fs=13)
# Desktop <-> Board: WebRTC P2P (двунаправленная)
c.poly([(1380, 275), (1380, 560)], marker='arr')
c.poly([(1400, 560), (1400, 275)], marker='arr')
c.text(1418, 398, 'WebRTC:', fs=13, anchor='start')
c.text(1418, 416, 'видео + data-', fs=13, anchor='start')
c.text(1418, 434, 'каналы (P2P,', fs=13, anchor='start')
c.text(1418, 452, 'STUN/TURN)', fs=13, anchor='start')

out = pathlib.Path(__file__).parent / 'c4_container.svg'
out.write_text(c.svg('Рисунок 3 – Диаграмма контейнеров (C4 Level 2) системы Mavix'), encoding='utf-8')
print(out)
