#!/usr/bin/env python3
"""UML Activity (диаграмма деятельности) — процесс доставки в Mavix.

Нотация: начальный узел (закрашенный круг), действия (скруглённые
прямоугольники), решение/слияние (ромб) с охранными условиями [..],
разделение/слияние потоков fork/join (закрашенная полоса), конечный узел
(круг в кольце). Поток управления — линия с открытым наконечником.
"""
from __future__ import annotations

import pathlib
import types

from diagramlib import Canvas

c = Canvas(1180, 1320)


def initial(cx, cy):
    c.add(f'<circle cx="{cx}" cy="{cy}" r="11" fill="#000"/>')
    return types.SimpleNamespace(cx=cx, b=cy + 11, t=cy - 11)


def final(cx, cy):
    c.add(f'<circle cx="{cx}" cy="{cy}" r="13" fill="none" stroke="#000" stroke-width="1.3"/>')
    c.add(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#000"/>')
    return types.SimpleNamespace(cx=cx, t=cy - 13, l=cx - 13, r=cx + 13)


def action(x, y, w, h, lines):
    c.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" ry="16" '
          f'stroke="#000" fill="none" stroke-width="1.2"/>')
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * 9 + 5
    for i, ln in enumerate(lines):
        c.text(x + w / 2, y0 + i * 18, ln, fs=13.5)
    return types.SimpleNamespace(cx=x + w / 2, t=y, b=y + h, l=x, r=x + w, cy=y + h / 2)


def decision(cx, cy, hw, hh, text):
    pts = f'{cx},{cy-hh} {cx+hw},{cy} {cx},{cy+hh} {cx-hw},{cy}'
    c.add(f'<polygon points="{pts}" stroke="#000" fill="none" stroke-width="1.2"/>')
    lines = text if isinstance(text, list) else [text]
    y0 = cy - (len(lines) - 1) * 9 + 4
    for i, ln in enumerate(lines):
        c.text(cx, y0 + i * 18, ln, fs=12.5)
    return types.SimpleNamespace(cx=cx, cy=cy, t=cy - hh, b=cy + hh, l=cx - hw, r=cx + hw)


def bar(cx, cy, w):
    c.add(f'<rect x="{cx-w/2}" y="{cy-4}" width="{w}" height="8" fill="#000"/>')
    return types.SimpleNamespace(cx=cx, t=cy - 4, b=cy + 4, l=cx - w / 2, r=cx + w / 2)


def flow(pts, guard=None, gx=0, gy=0, anchor='start'):
    c.poly(pts, marker='open')
    if guard:
        c.text(gx, gy, guard, fs=12, anchor=anchor, italic=True)


CX = 560
ini = initial(CX, 80)
a1 = action(400, 120, 320, 56, ['Администратор: создать заявку (дрон, адрес)'])
a2 = action(400, 220, 320, 56, ['Сервер: разослать операторам (offered)'])
a3 = action(400, 320, 320, 56, ['Оператор: принять заявку'])
d = decision(CX, 440, 130, 56, ['заявка ещё', 'offered?'])
fin_no = final(900, 440)
a4 = action(400, 540, 320, 56, ['Сервер: захватить заявку (accepted)'])
a5 = action(400, 640, 320, 56, ['Оператор: подключиться к дрону (WebRTC)'])
fk = bar(CX, 735, 520)
pl = action(300, 775, 240, 60, ['Борт: видео', 'и телеметрия'])
pr = action(620, 775, 240, 60, ['Оператор:', 'управление дроном'])
jn = bar(CX, 885, 520)
a6 = action(400, 925, 320, 56, ['Оператор: сброс груза у точки'])
a7 = action(400, 1025, 320, 56, ['Борт: исполнить сброс (AUX-канал)'])
a8 = action(400, 1125, 320, 56, ['Сервер: отметить delivered, уведомить'])
fin = final(CX, 1235)

# Потоки
flow([(ini.cx, ini.b), (a1.cx, a1.t)])
flow([(a1.cx, a1.b), (a2.cx, a2.t)])
flow([(a2.cx, a2.b), (a3.cx, a3.t)])
flow([(a3.cx, a3.b), (d.cx, d.t)])
flow([(d.r, d.cy), (fin_no.l, d.cy)], '[нет — забрал другой]', d.r + 14, d.cy - 8, 'start')
flow([(d.cx, d.b), (a4.cx, a4.t)], '[да]', d.cx + 12, (d.b + a4.t) / 2, 'start')
flow([(a4.cx, a4.b), (a5.cx, a5.t)])
flow([(a5.cx, a5.b), (fk.cx, fk.t)])
flow([(330, fk.b), (330, pl.t)])
flow([(700, fk.b), (700, pr.t)])
flow([(pl.cx, pl.b), (pl.cx, jn.t)])
flow([(pr.cx, pr.b), (pr.cx, jn.t)])
flow([(jn.cx, jn.b), (a6.cx, a6.t)])
flow([(a6.cx, a6.b), (a7.cx, a7.t)])
flow([(a7.cx, a7.b), (a8.cx, a8.t)])
flow([(a8.cx, a8.b), (fin.cx, fin.t)])

out = pathlib.Path(__file__).parent / 'activity.svg'
out.write_text(c.svg('Рисунок 13 – Диаграмма деятельности (UML Activity): процесс доставки'), encoding='utf-8')
print(out)
