#!/usr/bin/env python3
"""DFD (нотация Гейна–Сарсона) — потоки данных системы Mavix.

Внешние сущности — прямоугольники; процессы — скруглённые блоки с номером;
хранилища — открытые справа прямоугольники с ячейкой Dn; потоки — помеченные
направленные стрелки.
"""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1680, 800)


def ext(x, y, w, h, lines):
    c.rect(x, y, w, h, sw=1.4)
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * 9 + 5
    for i, ln in enumerate(lines):
        c.text(x + w / 2, y0 + i * 18, ln, fs=14, bold=True)
    return type('B', (), {'l': x, 'r': x + w, 't': y, 'b': y + h, 'cx': x + w / 2, 'cy': y + h / 2})


def proc(x, y, w, h, num, lines):
    c.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" ry="14" '
          f'stroke="#000" fill="none" stroke-width="1.3"/>')
    c.add(f'<line x1="{x}" y1="{y+26}" x2="{x+34}" y2="{y+26}" stroke="#000" stroke-width="1.0"/>')
    c.add(f'<line x1="{x+34}" y1="{y}" x2="{x+34}" y2="{y+26}" stroke="#000" stroke-width="1.0"/>')
    c.text(x + 17, y + 18, str(num), fs=13, bold=True)
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * 9 + 9
    for i, ln in enumerate(lines):
        c.text(x + w / 2 + 8, y0 + i * 18, ln, fs=13.5, bold=True)
    return type('B', (), {'l': x, 'r': x + w, 't': y, 'b': y + h, 'cx': x + w / 2, 'cy': y + h / 2})


def store(x, y, w, h, did, name):
    c.line(x, y, x + w, y)            # верх
    c.line(x, y + h, x + w, y + h)    # низ
    c.line(x, y, x, y + h)            # левая
    c.line(x + 40, y, x + 40, y + h)  # ячейка ID
    c.text(x + 20, y + h / 2 + 5, did, fs=13, bold=True)
    c.text(x + 40 + (w - 40) / 2, y + h / 2 + 5, name, fs=13)
    return type('B', (), {'l': x, 'r': x + w, 't': y, 'b': y + h, 'cx': x + w / 2, 'cy': y + h / 2})


def flow(pts, label, lx, ly, anchor='middle'):
    c.poly(pts, marker='arr')
    c.text(lx, ly, label, fs=12, anchor=anchor)


# Внешние сущности
adm = ext(60, 120, 175, 80, ['Администратор'])
op = ext(60, 560, 175, 80, ['Оператор'])
drone = ext(1470, 560, 150, 120, ['Дрон', '(борт)'])
# Процессы
P1 = proc(360, 330, 210, 90, 1, ['Аутенти-', 'фикация'])
P2 = proc(660, 120, 230, 95, 2, ['Управление', 'парком'])
P3 = proc(660, 360, 250, 110, 3, ['Управление', 'доставками'])
P4 = proc(1120, 560, 260, 120, 4, ['Связь и', 'пилотирование'])
# Хранилища
D1 = store(1000, 135, 330, 46, 'D1', 'Учётные записи и парк')
D2 = store(1000, 400, 330, 46, 'D2', 'Доставки (журнал)')

# --- потоки -------------------------------------------------------------------
# Аутентификация
flow([(adm.r, 360), (P1.l, 360)], 'учётные данные', (adm.r + P1.l) / 2, 350)
flow([(op.r, 600), (300, 600), (300, 395), (P1.l, 395)], 'учётные данные', 250, 470, 'start')
# Парк
flow([(adm.r, 160), (P2.l, 160)], 'оператор / дрон', (adm.r + P2.l) / 2, 150)
flow([(P2.r, 168), (D1.l, 168)], 'записи', (P2.r + D1.l) / 2, 158)
# Доставки
flow([(adm.r, 185), (600, 185), (600, 385), (P3.l, 385)], 'новая заявка', 612, 300, 'start')
flow([(op.r, 615), (620, 615), (620, 450), (P3.l, 450)], 'принять заявку', 632, 540, 'start')
flow([(P3.r, 415), (D2.l, 415)], 'заявка / статус', (P3.r + D2.l) / 2, 405)
# Связь и пилотирование
flow([(P3.cx, P3.b), (P3.cx, 620), (P4.l, 620)], 'drone_id', P3.cx + 12, 540, 'start')
flow([(op.r, 640), (540, 640), (540, 700), (P4.l, 700)], 'команды (джойстик)', 770, 712, 'middle')
flow([(P4.l, 600), (980, 600), (980, 520), (op.r + 5, 520), (op.r + 5, op.b)], 'видео, телеметрия', 700, 510, 'middle')
flow([(drone.l, 600), (P4.r, 600)], 'видео + телеметрия', (drone.l + P4.r) / 2, 590)
flow([(P4.r, 640), (drone.l, 640)], 'команды (CRSF/MAVLink)', (drone.l + P4.r) / 2, 660)
flow([(P4.cx, P4.t), (P4.cx, 512), (820, 512), (820, P3.b)], 'статус доставки', 1010, 504, 'middle')

out = pathlib.Path(__file__).parent / 'dfd.svg'
out.write_text(c.svg('Рисунок 12 – Диаграмма потоков данных (DFD) системы Mavix'), encoding='utf-8')
print(out)
