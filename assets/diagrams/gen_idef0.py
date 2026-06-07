#!/usr/bin/env python3
"""IDEF0 (SADT) — функциональная модель A0 системы Mavix с ICOM-стрелками.

ICOM: Input — слева, Control — сверху, Output — справа, Mechanism — снизу.
"""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1680, 900)


def fbox(x, y, lines, num, w=250, h=92):
    c.rect(x, y, w, h, sw=1.3)
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * 9 + 5
    for i, ln in enumerate(lines):
        c.text(x + w / 2, y0 + i * 18, ln, fs=14, bold=True)
    c.text(x + w - 8, y + h - 9, num, fs=13, anchor='end', italic=True)
    return type('B', (), {'x': x, 'y': y, 'w': w, 'h': h, 'cx': x + w / 2,
                          'l': x, 'r': x + w, 't': y, 'b': y + h})


A1 = fbox(170, 150, ['Аутентификация и', 'управление парком'], 'A1')
A2 = fbox(520, 300, ['Формирование и', 'распределение заявок'], 'A2')
A3 = fbox(880, 450, ['Установление', 'WebRTC-связи'], 'A3')
A4 = fbox(1240, 600, ['Пилотирование и', 'доставка груза'], 'A4', w=260)

# --- внутренние потоки (Output → Input, лесенкой) -----------------------------
c.poly([(A1.r, A1.t + 46), (A1.r + 50, A1.t + 46), (A1.r + 50, A2.t + 46), (A2.l, A2.t + 46)], marker='arr')
c.text(A1.r + 58, A1.t + 110, 'операторы,', fs=12, anchor='start')
c.text(A1.r + 58, A1.t + 128, 'дроны (парк)', fs=12, anchor='start')
c.poly([(A2.r, A2.t + 46), (A2.r + 55, A2.t + 46), (A2.r + 55, A3.t + 46), (A3.l, A3.t + 46)], marker='arr')
c.text(A2.r + 63, A2.t + 110, 'принятая', fs=12, anchor='start')
c.text(A2.r + 63, A2.t + 128, 'заявка', fs=12, anchor='start')
c.poly([(A3.r, A3.t + 46), (A3.r + 55, A3.t + 46), (A3.r + 55, A4.t + 46), (A4.l, A4.t + 46)], marker='arr')
c.text(A3.r + 63, A3.t + 110, 'WebRTC-', fs=12, anchor='start')
c.text(A3.r + 63, A3.t + 128, 'сессия', fs=12, anchor='start')

# --- Control (сверху вниз в верх блоков) --------------------------------------
ctrl = [(A1, 'Роли и доступ (JWT)'), (A2, 'Политика приёма «такси»'),
        (A3, 'Регламенты связи'), (A4, 'Регламенты полёта / failsafe')]
for b, lbl in ctrl:
    c.poly([(b.cx, b.t - 48), (b.cx, b.t)], marker='arr')
    c.text(b.cx, b.t - 54, lbl, fs=12)

# --- Input (слева в A1) -------------------------------------------------------
c.poly([(30, A1.t + 46), (A1.l, A1.t + 46)], marker='arr')
c.text(30, A1.t + 18, 'Запросы оператора', fs=12, anchor='start')
c.text(30, A1.t + 34, 'и администратора', fs=12, anchor='start')

# --- Output (справа из A4) ----------------------------------------------------
c.poly([(A4.r, A4.t + 46), (1640, A4.t + 46)], marker='arr')
c.text(A4.r + 14, A4.t + 18, 'Доставленный груз,', fs=12, anchor='start')
c.text(A4.r + 14, A4.t + 34, 'журнал, телеметрия', fs=12, anchor='start')

# --- Mechanism (снизу вверх в низ блоков) -------------------------------------
mech = [(A1, 'MavixServer, MavixWeb'), (A2, 'MavixServer (БД)'),
        (A3, 'Сигналинг, STUN/TURN'), (A4, 'Desktop · Board · QGC · оператор')]
for b, lbl in mech:
    c.poly([(b.cx, b.b + 46), (b.cx, b.b)], marker='arr')
    c.text(b.cx, b.b + 62, lbl, fs=12)

out = pathlib.Path(__file__).parent / 'idef0.svg'
out.write_text(c.svg('Рисунок 11 – Функциональная модель IDEF0 (диаграмма A0) системы Mavix'), encoding='utf-8')
print(out)
