#!/usr/bin/env python3
"""C4 уровень 1 — контекст системы Mavix."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1500, 940)

# Система (в скоупе)
SX, SY, SW, SH = 560, 360, 380, 140
c.box(SX, SY, SW, SH, 'Система Mavix', None, sw=1.6, title_fs=18)
c.text(SX + SW / 2, SY + SH / 2 + 28, 'Автоматизированная доставка', fs=14, italic=True)
c.text(SX + SW / 2, SY + SH / 2 + 46, 'малогабаритных грузов дронами', fs=14, italic=True)
sx_cx = SX + SW / 2

# Акторы
c.actor(180, 70, 'Администратор')
c.actor(1320, 70, 'Оператор')

# Внешние системы (вне скоупа)
ext = [
    (60, 'SMTP-сервер', 'почта'),
    (430, 'STUN / TURN', 'NAT traversal'),
    (800, 'Nominatim', 'геокодирование'),
    (1170, 'QGroundControl', 'MAVLink-полёт'),
]
EW, EH, EY = 270, 100, 740
ext_geom = {}
for ex, name, sub in ext:
    c.rect(ex, EY, EW, EH, sw=1.2)
    c.text(ex + EW / 2, EY + 36, name, fs=16, bold=True)
    c.text(ex + EW / 2, EY + 58, sub, fs=13, italic=True)
    c.text(ex + EW / 2, EY + 80, '(вне скоупа ВКР)', fs=12, italic=True)
    ext_geom[name] = (ex + EW / 2, EY)

# Связи акторов с системой (стрелки в систему)
c.poly([(230, 165), (sx_cx - 60, 165), (sx_cx - 60, SY)], marker='arr')
c.text(300, 150, 'HTTPS: операторы, дроны, заявки', fs=14, anchor='start')
c.poly([(1270, 165), (sx_cx + 60, 165), (sx_cx + 60, SY)], marker='arr')
c.text(1248, 132, 'Веб/Desktop: приём заявок,', fs=14, anchor='end')
c.text(1248, 150, 'видео + телеметрия (WebRTC)', fs=14, anchor='end')

# Связи системы с внешними (вниз)
labels = {
    'SMTP-сервер': 'письма операторам',
    'STUN / TURN': 'ICE-кандидаты',
    'Nominatim': 'обратное геокодирование',
}
for name in ('SMTP-сервер', 'STUN / TURN', 'Nominatim'):
    tx, ty = ext_geom[name]
    c.poly([(sx_cx, SY + SH), (sx_cx, 640), (tx, 640), (tx, ty)], marker='arr')
    c.text(tx + 16, 700, labels[name], fs=13, anchor='start')

# Оператор ↔ QGroundControl
qx, qy = ext_geom['QGroundControl']
c.poly([(1320, 218), (1320, 690), (qx, 690), (qx, qy)], marker='arr')
c.text(qx + 16, 700, 'ручной MAVLink-полёт', fs=13, anchor='start')

out = pathlib.Path(__file__).parent / 'c4_context.svg'
out.write_text(c.svg('Рисунок 2 – Контекстная диаграмма (C4 Level 1) системы Mavix'), encoding='utf-8')
print(out)
