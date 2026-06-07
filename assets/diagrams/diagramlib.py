#!/usr/bin/env python3
"""Примитивы для чёрно-белых диаграмм ВКР (см. RULES.md).

Только stroke:#000 на белом, Times-метрики (Liberation Serif). Все
координаты явные — раскладку контролирует вызывающий скрипт.
"""
from __future__ import annotations

import math

FONT = 'Liberation Serif, Times New Roman, serif'


def _esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def twidth(s: str, fs: float) -> float:
    """Грубая оценка ширины строки (кириллица ×1.15)."""
    w = 0.0
    for c in s:
        k = 1.15 if ('а' <= c.lower() <= 'я' or c == 'ё') else 0.6
        w += fs * (k if k > 1 else 0.58)
    return w


class Canvas:
    def __init__(self, w: int, h: int) -> None:
        self.w, self.h = w, h
        self.items: list[str] = []

    def add(self, s: str) -> None:
        self.items.append(s)

    def text(self, x, y, s, fs=15, anchor='middle', italic=False, bold=False) -> None:
        st = []
        if italic:
            st.append('font-style="italic"')
        if bold:
            st.append('font-weight="bold"')
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
                 f'font-size="{fs}" {" ".join(st)}>{_esc(s)}</text>')

    def line(self, x1, y1, x2, y2, sw=0.9, dash=False) -> None:
        d = ' stroke-dasharray="6 5"' if dash else ''
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="#000" stroke-width="{sw}"{d}/>')

    def arrowhead(self, x, y, dx, dy, open=False) -> None:
        """Наконечник стрелки явным полигоном (НЕ через <marker> — QtSvg их
        рендерит неверно). (dx,dy) — направление движения линии в точку (x,y)."""
        a = math.atan2(dy, dx)
        L, W = 12.0, 5.0
        bx, by = x - L * math.cos(a), y - L * math.sin(a)
        nx, ny = -math.sin(a) * W, math.cos(a) * W
        p1 = (bx + nx, by + ny)
        p2 = (bx - nx, by - ny)
        if open:  # открытый (реализация/ответ/include/extend) — две черты
            self.line(p1[0], p1[1], x, y, sw=0.9)
            self.line(p2[0], p2[1], x, y, sw=0.9)
        else:     # закрашенный треугольник (ассоциация/синхронный вызов)
            self.add(f'<polygon points="{x:.1f},{y:.1f} {p1[0]:.1f},{p1[1]:.1f} '
                     f'{p2[0]:.1f},{p2[1]:.1f}" fill="#000" stroke="#000" stroke-width="0.6"/>')

    def hollow_triangle(self, x, y, dx, dy) -> None:
        """Полый треугольник UML (обобщение/реализация) у родителя/интерфейса."""
        a = math.atan2(dy, dx)
        L, W = 15.0, 7.0
        bx, by = x - L * math.cos(a), y - L * math.sin(a)
        nx, ny = -math.sin(a) * W, math.cos(a) * W
        self.add(f'<polygon points="{x:.1f},{y:.1f} {bx+nx:.1f},{by+ny:.1f} '
                 f'{bx-nx:.1f},{by-ny:.1f}" fill="#fff" stroke="#000" stroke-width="1.0"/>')

    def diamond(self, x, y, dx, dy, filled=True) -> None:
        """Ромб UML: filled — композиция, hollow — агрегация. У «целого»."""
        a = math.atan2(dy, dx)
        L, W = 9.0, 6.0
        tx, ty = x + L * math.cos(a), y + L * math.sin(a)          # дальняя вершина
        nx, ny = -math.sin(a) * W, math.cos(a) * W
        s1 = (x + L / 2 * math.cos(a) + nx, y + L / 2 * math.sin(a) + ny)
        s2 = (x + L / 2 * math.cos(a) - nx, y + L / 2 * math.sin(a) - ny)
        fill = '#000' if filled else '#fff'
        self.add(f'<polygon points="{x:.1f},{y:.1f} {s1[0]:.1f},{s1[1]:.1f} '
                 f'{tx:.1f},{ty:.1f} {s2[0]:.1f},{s2[1]:.1f}" fill="{fill}" stroke="#000" stroke-width="1.0"/>')

    def poly(self, pts, sw=0.9, marker=None, dash=False, gap=14) -> None:
        # Наконечник рисуем САМИ полигоном со СДВИГОМ на gap наружу от цели —
        # стрелка стоит снаружи блока с отступом, не сливается с границей.
        pts = [(float(x), float(y)) for x, y in pts]
        head = None
        if marker and len(pts) >= 2:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            dx, dy = x2 - x1, y2 - y1
            dist = (dx * dx + dy * dy) ** 0.5 or 1.0
            ux, uy = dx / dist, dy / dist
            tx, ty = x2 - ux * gap, y2 - uy * gap   # кончик с отступом
            pts[-1] = (tx, ty)
            head = (tx, ty, ux, uy)
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        d = ' stroke-dasharray="6 5"' if dash else ''
        self.add(f'<polyline points="{p}" stroke="#000" fill="none" stroke-width="{sw}"{d}/>')
        if head:
            self.arrowhead(head[0], head[1], head[2], head[3], open=(marker == 'open'))

    def rect(self, x, y, w, h, sw=1.2) -> None:
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'stroke="#000" fill="none" stroke-width="{sw}"/>')

    def box(self, x, y, w, h, title, tech=None, sw=1.2, title_fs=17) -> None:
        """Блок C4/компонента: имя (bold) + опц. стек/описание (italic)."""
        self.rect(x, y, w, h, sw)
        if tech:
            self.text(x + w / 2, y + h / 2 - 4, title, fs=title_fs, bold=True)
            self.text(x + w / 2, y + h / 2 + 16, tech, fs=14, italic=True)
        else:
            self.text(x + w / 2, y + h / 2 + 5, title, fs=title_fs, bold=True)

    def box_multi(self, x, y, w, h, lines, sw=1.2) -> None:
        """Блок с несколькими строками (1-я — bold имя, остальные italic)."""
        self.rect(x, y, w, h, sw)
        n = len(lines)
        y0 = y + h / 2 - (n - 1) * 9 + 5
        for i, ln in enumerate(lines):
            self.text(x + w / 2, y0 + i * 18, ln, fs=(16 if i == 0 else 13),
                      bold=(i == 0), italic=(i > 0))

    def node3d(self, x, y, w, h, title, stereo='device', d=16) -> None:
        """UML-узел развёртывания — 3D-коробка со стереотипом сверху."""
        self.rect(x, y, w, h, sw=1.5)
        self.add(f'<polygon points="{x:.0f},{y:.0f} {x+d:.0f},{y-d:.0f} '
                 f'{x+w+d:.0f},{y-d:.0f} {x+w:.0f},{y:.0f}" fill="none" stroke="#000" stroke-width="1.5"/>')
        self.add(f'<polygon points="{x+w:.0f},{y:.0f} {x+w+d:.0f},{y-d:.0f} '
                 f'{x+w+d:.0f},{y+h-d:.0f} {x+w:.0f},{y+h:.0f}" fill="none" stroke="#000" stroke-width="1.5"/>')
        self.text(x + w / 2, y + 17, f'«{stereo}»', fs=11, italic=True)
        self.text(x + w / 2, y + 35, title, fs=15, bold=True)

    def artifact(self, x, y, w, h, title, sub=None, stereo='artifact') -> None:
        """UML-артефакт (или вложенный узел) — прямоугольник со стереотипом."""
        self.rect(x, y, w, h, sw=1.1)
        self.text(x + w / 2, y + 15, f'«{stereo}»', fs=10, italic=True)
        if sub:
            self.text(x + w / 2, y + h / 2 + 4, title, fs=13.5, bold=True)
            self.text(x + w / 2, y + h / 2 + 21, sub, fs=11.5, italic=True)
        else:
            self.text(x + w / 2, y + h / 2 + 9, title, fs=13.5, bold=True)

    def actor(self, cx, top, name) -> None:
        """Stick-figure актор; name под фигурой (может быть list из 2 строк)."""
        r = 11
        hy = top + r
        self.add(f'<circle cx="{cx}" cy="{hy}" r="{r}" stroke="#000" fill="none" stroke-width="1.1"/>')
        body_top = hy + r
        body_bot = body_top + 34
        self.line(cx, body_top, cx, body_bot, sw=1.1)            # тело
        self.line(cx - 20, body_top + 12, cx + 20, body_top + 12, sw=1.1)  # руки
        self.line(cx, body_bot, cx - 16, body_bot + 22, sw=1.1)  # нога
        self.line(cx, body_bot, cx + 16, body_bot + 22, sw=1.1)  # нога
        names = name if isinstance(name, list) else [name]
        for i, nm in enumerate(names):
            self.text(cx, body_bot + 42 + i * 19, nm, fs=17)

    def ellipse(self, cx, cy, rx, ry, text) -> None:
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" stroke="#000" '
                 f'fill="none" stroke-width="1.1"/>')
        lines = text if isinstance(text, list) else [text]
        y0 = cy - (len(lines) - 1) * 9 + 5
        for i, ln in enumerate(lines):
            self.text(cx, y0 + i * 18, ln, fs=15)

    def svg(self, caption: str) -> str:
        defs = (
            '<defs>'
            '<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" '
            'markerHeight="9" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#000"/></marker>'
            '<marker id="open" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="11" '
            'markerHeight="11" orient="auto"><path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="#000"/></marker>'
            '</defs>'
        )
        cap = (f'<text x="{self.w/2}" y="{self.h-22}" text-anchor="middle" font-style="italic" '
               f'font-size="17">{_esc(caption)}</text>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">\n'
                f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>\n{defs}\n'
                + '\n'.join(self.items) + '\n' + cap + '\n</svg>\n')
