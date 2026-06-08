#!/usr/bin/env python3
"""Схема подключения борта: Raspberry Pi — полётный контроллер (CRSF по UART),
камера и готовый серво-сбрасыватель груза на AUX-канале."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1320, 760)

# Raspberry Pi
c.rect(180, 250, 280, 210, sw=1.4)
c.text(320, 282, 'Raspberry Pi', fs=16, bold=True)
c.text(440, 318, 'пин 8 · GPIO14 (TX)', fs=12.5, anchor='end')
c.text(440, 360, 'пин 10 · GPIO15 (RX)', fs=12.5, anchor='end')
c.text(440, 402, 'пин 6 (GND)', fs=12.5, anchor='end')

# Полётный контроллер
c.rect(860, 250, 280, 210, sw=1.4)
c.text(1000, 282, 'Полётный контроллер', fs=16, bold=True)
c.text(1000, 300, '(Betaflight / iNav / PX4)', fs=12, italic=True)
c.text(872, 318, 'T (TX)', fs=12.5, anchor='start')
c.text(872, 360, 'R (RX)', fs=12.5, anchor='start')
c.text(872, 402, 'GND', fs=12.5, anchor='start')
c.text(872, 444, 'AUX (CH8, PWM)', fs=12.5, anchor='start')

# Провода UART (крест-накрест, 3.3 В, без преобразователя уровней)
c.line(460, 318, 860, 360, sw=1.1)   # RPi TX -> FC R(RX)
c.line(460, 360, 860, 318, sw=1.1)   # FC T(TX) -> RPi RX
c.line(460, 402, 860, 402, sw=1.1)   # GND
c.text(660, 330, 'TX → RX', fs=12, anchor='middle')
c.text(660, 392, 'RX ← TX', fs=12, anchor='middle')
c.text(660, 418, 'GND', fs=12, anchor='middle')
c.text(660, 470, '3.3 В · перекрёстно · преобразователь уровней не нужен', fs=12, italic=True)

# Камера -> RPi
c.box(180, 90, 280, 80, 'Камера', 'USB / CSI', sw=1.2, title_fs=15)
c.poly([(320, 170), (320, 250)], marker='arr')
c.text(332, 215, 'видеопоток', fs=12, anchor='start')

# FC -> серво-сбрасыватель (готовое решение)
c.box(860, 560, 280, 90, 'Серво-сбрасыватель', '(готовый модуль)', sw=1.2, title_fs=15)
c.poly([(1000, 460), (1000, 560)], marker='arr')
c.text(1012, 515, 'PWM по CH8 (AUX)', fs=12, anchor='start')

out = pathlib.Path(__file__).parent / 'wiring.svg'
out.write_text(c.svg('Рисунок 2 – Схема подключения борта (RPi, полётный контроллер, камера, сброс груза)'), encoding='utf-8')
print(out)
