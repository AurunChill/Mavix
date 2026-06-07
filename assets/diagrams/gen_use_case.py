#!/usr/bin/env python3
"""UML Use Case — администратор и оператор системы Mavix."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1500, 1000)
RX, RY = 138, 42

# Граница системы
c.rect(360, 70, 780, 850, sw=1.6)
c.text(750, 102, 'Mavix', fs=18, bold=True)

# Акторы
c.actor(165, 390, 'Администратор')
c.actor(1335, 390, 'Оператор')

# Общий сценарий
shared = (750, 185)
c.ellipse(*shared, RX, RY, 'Вход в систему')

# Сценарии администратора (левая колонка)
admin_uc = [
    (575, 305, ['Создать', 'оператора']),
    (575, 415, ['Скачать дистрибутив', 'борта']),
    (575, 525, ['Создать заявку', 'на доставку']),
    (575, 635, ['Журнал', 'доставок']),
    (575, 745, ['Управление', 'дронами']),
]
# Сценарии оператора (правая колонка)
op_uc = [
    (925, 360, ['Принять', 'заявку']),
    (925, 510, ['Управление дроном', '(видео, телеметрия)']),
    (925, 660, ['Сбросить', 'груз']),
]
for x, y, t in admin_uc + op_uc:
    c.ellipse(x, y, RX, RY, t)

# Ассоциации актор—сценарий (прямые линии, классика use-case)
ax, ay = 205, 455   # точка выхода у администратора
for x, y, _ in admin_uc:
    c.line(ax, ay, x - RX, y, sw=0.9)
c.line(ax, ay, shared[0] - RX + 8, shared[1] + 22, sw=0.9)

ox, oy = 1295, 455  # точка выхода у оператора
for x, y, _ in op_uc:
    c.line(ox, oy, x + RX, y, sw=0.9)
c.line(ox, oy, shared[0] + RX - 8, shared[1] + 22, sw=0.9)

out = pathlib.Path(__file__).parent / 'use_case.svg'
out.write_text(c.svg('Рисунок 5 – Диаграмма вариантов использования (Use Case) системы Mavix'), encoding='utf-8')
print(out)
