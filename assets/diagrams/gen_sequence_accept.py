#!/usr/bin/env python3
"""UML Sequence — приём заявки оператором и подключение к дрону."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1540, 760)
TOP = 70
BOT = 660

parts = [
    (210, 'Оператор', '(MavixDesktop)'),
    (640, 'MavixServer', None),
    (1020, 'PostgreSQL', None),
    (1370, 'MavixBoard', None),
]
cxs = {}
for cx, name, sub in parts:
    w = 230
    c.rect(cx - w / 2, TOP, w, 56, sw=1.2)
    if sub:
        c.text(cx, TOP + 24, name, fs=15, bold=True)
        c.text(cx, TOP + 42, sub, fs=12, italic=True)
    else:
        c.text(cx, TOP + 33, name, fs=15, bold=True)
    c.line(cx, TOP + 56, cx, BOT, sw=0.8, dash=True)  # lifeline
    cxs[name] = cx


def msg(y, a, b, lines, ret=False):
    x1, x2 = cxs[a], cxs[b]
    c.poly([(x1, y), (x2, y)], marker=('open' if ret else 'arr'), dash=ret)
    mid = (x1 + x2) / 2
    if isinstance(lines, str):
        lines = [lines]
    y0 = y - 10 - 18 * (len(lines) - 1)
    for i, ln in enumerate(lines):
        c.text(mid, y0 + i * 18, ln, fs=13)


msg(170, 'Оператор', 'MavixServer', "1. POST /deliveries/{id}/accept (Bearer JWT)")
msg(258, 'MavixServer', 'PostgreSQL', ["2. UPDATE deliveries SET status='accepted'",
                                       "WHERE status='offered' (атомарный захват)"])
msg(330, 'PostgreSQL', 'MavixServer', "3. rowcount = 1 — заявка захвачена", ret=True)
msg(400, 'MavixServer', 'Оператор', "4. 200 OK + delivery (status=accepted)", ret=True)
msg(470, 'Оператор', 'MavixServer', "5. WS: { type: 'connect', drone_id }")
msg(540, 'MavixServer', 'MavixBoard', "6. WS: { type: 'connect', gcs_id }")

c.text(640, 615, 'Далее — установление WebRTC-сессии (см. рис. 10)', fs=13, italic=True)

out = pathlib.Path(__file__).parent / 'sequence_accept.svg'
out.write_text(c.svg('Рисунок 9 – Диаграмма последовательности: приём заявки и подключение к дрону'), encoding='utf-8')
print(out)
