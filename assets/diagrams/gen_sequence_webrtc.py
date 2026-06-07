#!/usr/bin/env python3
"""UML Sequence — установление WebRTC-сессии (сигналинг offer/answer/ICE)."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1520, 900)
TOP = 70
BOT = 810

parts = [(250, 'MavixDesktop', '(оператор)'), (760, 'MavixServer', '(сигналинг)'),
         (1270, 'MavixBoard', '(борт)')]
cxs = {}
for cx, name, sub in parts:
    w = 240
    c.rect(cx - w / 2, TOP, w, 56, sw=1.2)
    c.text(cx, TOP + 24, name, fs=15, bold=True)
    c.text(cx, TOP + 42, sub, fs=12, italic=True)
    c.line(cx, TOP + 56, cx, BOT, sw=0.8, dash=True)
    cxs[name] = cx


def msg(y, a, b, text, ret=False):
    x1, x2 = cxs[a], cxs[b]
    c.poly([(x1, y), (x2, y)], marker=('open' if ret else 'arr'), dash=ret)
    c.text((x1 + x2) / 2, y - 9, text, fs=13)


def selfmsg(y, who, text, side='right'):
    x = cxs[who]
    d = 1 if side == 'right' else -1
    c.poly([(x, y), (x + d * 34, y), (x + d * 34, y + 20), (x, y + 20)], marker='arr')
    c.text(x + d * 44, y + 6, text, fs=13, anchor=('start' if side == 'right' else 'end'))


msg(165, 'MavixDesktop', 'MavixServer', "1. WS connect { drone_id }")
msg(225, 'MavixServer', 'MavixBoard', "2. WS connect { gcs_id }")
selfmsg(265, 'MavixBoard', "3. пайплайн → PLAYING; start_session()", side='left')
msg(360, 'MavixBoard', 'MavixServer', "4. SDP offer")
msg(420, 'MavixServer', 'MavixDesktop', "5. SDP offer")
selfmsg(460, 'MavixDesktop', "6. setRemoteDescription; createAnswer")
msg(555, 'MavixDesktop', 'MavixServer', "7. SDP answer")
msg(615, 'MavixServer', 'MavixBoard', "8. SDP answer")
msg(680, 'MavixDesktop', 'MavixServer', "9. ICE-кандидаты (trickle)")
msg(740, 'MavixServer', 'MavixBoard', "10. ICE-кандидаты (trickle)")

c.text(760, 785, 'ICE завершено → data-каналы (packet/config/telemetry) открыты, видео H.264 идёт по WebRTC',
       fs=13, italic=True)

out = pathlib.Path(__file__).parent / 'sequence_webrtc.svg'
out.write_text(c.svg('Рисунок 10 – Диаграмма последовательности: установление WebRTC-сессии'), encoding='utf-8')
print(out)
