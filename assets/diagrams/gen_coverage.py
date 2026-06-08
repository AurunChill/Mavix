#!/usr/bin/env python3
"""Диаграмма покрытия кода тестами по компонентам (board, desktop, server)."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(900, 620)

X0, Y0, H = 150, 520, 400          # ось: Y0 — 0%, Y0-H — 100%
# оси
c.line(X0, Y0 - H, X0, Y0, sw=1.3)
c.line(X0, Y0, X0 + 640, Y0, sw=1.3)
for pct in range(0, 101, 20):
    y = Y0 - H * pct / 100
    c.line(X0 - 6, y, X0, y, sw=0.8)
    c.text(X0 - 16, y + 5, f'{pct}', fs=12, anchor='end')
c.text(X0 - 44, Y0 - H / 2, '%', fs=13, anchor='middle')

bars = [('MavixBoard', 81, '299 тестов'),
        ('MavixDesktop', 72, '281 тест'),
        ('MavixServer', 80, '341 тест')]
bw, gap = 130, 80
x = X0 + 70
for name, pct, sub in bars:
    h = H * pct / 100
    c.rect(x, Y0 - h, bw, h, sw=1.2)
    c.text(x + bw / 2, Y0 - h - 14, f'{pct}%', fs=15, bold=True)
    c.text(x + bw / 2, Y0 + 24, name, fs=13)
    c.text(x + bw / 2, Y0 + 44, sub, fs=11.5, italic=True)
    x += bw + gap

out = pathlib.Path(__file__).parent / 'coverage.svg'
out.write_text(c.svg('Рисунок — Покрытие кода тестами по компонентам'), encoding='utf-8')
print(out)
