#!/usr/bin/env python3
"""Примитивы для чёрно-белых диаграмм ВКР (см. RULES.md).

Только stroke:#000 на белом, Times-метрики (Liberation Serif). Все
координаты явные — раскладку контролирует вызывающий скрипт.
"""
from __future__ import annotations

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

    def poly(self, pts, sw=0.9, marker=None, dash=False) -> None:
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        d = ' stroke-dasharray="6 5"' if dash else ''
        m = f' marker-end="url(#{marker})"' if marker else ''
        self.add(f'<polyline points="{p}" stroke="#000" fill="none" stroke-width="{sw}"{d}{m}/>')

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
