#!/usr/bin/env python3
"""Генератор ER-диаграммы БД Mavix (IDEF1X-подобной) в строгом Ч/Б стиле ВКР.

Таблицы и их строки раскладываются программно (ширина колонок — по контенту),
поэтому текст гарантированно не перекрывается. Связи (crow's foot) разведены
ортогонально. Выводит SVG; PNG рендерится отдельно (svg2png.py / QtSvg).
"""
from __future__ import annotations

import types

FS_TITLE = 17
FS_ROW = 14
ROW_H = 24
TITLE_H = 28
PAD = 10

# Колонки таблицы: атрибут / тип / ограничение.
COL = [185, 120, 70]
TABLE_W = sum(COL)


def _esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def table(x: float, y: float, name: str, rows: list[tuple[str, str, str]]) -> tuple[str, dict]:
    """Рисует таблицу. Возвращает (svg, geom) — geom с краями для связей."""
    h = TITLE_H + ROW_H * len(rows)
    parts = []
    # рамка
    parts.append(f'<rect x="{x}" y="{y}" width="{TABLE_W}" height="{h}" '
                 f'stroke="#000" fill="none" stroke-width="1.2"/>')
    # заголовок (italic, по центру)
    parts.append(f'<text x="{x + TABLE_W / 2:.1f}" y="{y + 19}" text-anchor="middle" '
                 f'font-style="italic" font-size="{FS_TITLE}" font-weight="bold">{_esc(name)}</text>')
    parts.append(f'<line x1="{x}" y1="{y + TITLE_H}" x2="{x + TABLE_W}" y2="{y + TITLE_H}" '
                 f'stroke="#000" stroke-width="1.1"/>')
    # вертикальные разделители колонок
    cx1 = x + COL[0]
    cx2 = x + COL[0] + COL[1]
    parts.append(f'<line x1="{cx1}" y1="{y + TITLE_H}" x2="{cx1}" y2="{y + h}" stroke="#000" stroke-width="0.7"/>')
    parts.append(f'<line x1="{cx2}" y1="{y + TITLE_H}" x2="{cx2}" y2="{y + h}" stroke="#000" stroke-width="0.7"/>')
    # строки
    ry = y + TITLE_H
    for attr, typ, con in rows:
        ty = ry + 16
        parts.append(f'<text x="{x + 8}" y="{ty}" font-size="{FS_ROW}">{_esc(attr)}</text>')
        parts.append(f'<text x="{cx1 + 8}" y="{ty}" font-size="{FS_ROW}" font-style="italic">{_esc(typ)}</text>')
        parts.append(f'<text x="{cx2 + 8}" y="{ty}" font-size="{FS_ROW}">{_esc(con)}</text>')
        ry += ROW_H
        if (attr, typ, con) != rows[-1]:
            parts.append(f'<line x1="{x}" y1="{ry}" x2="{x + TABLE_W}" y2="{ry}" stroke="#000" stroke-width="0.4"/>')
    geom = {'x': x, 'y': y, 'w': TABLE_W, 'h': h,
            'cx': x + TABLE_W / 2, 'cy': y + h / 2,
            'left': x, 'right': x + TABLE_W, 'top': y, 'bottom': y + h}
    return '\n'.join(parts), types.SimpleNamespace(**geom)


def crow_one(px: float, py: float, dx: int, dy: int) -> str:
    """Метка «1» — поперечная чёрточка на линии СНАРУЖИ таблицы.

    (dx, dy) — направление линии НАРУЖУ от края таблицы. Чёрточка ставится
    на 12 px вдоль этого направления (за пределами таблицы)."""
    if dx != 0:  # линия горизонтальна → чёрточка вертикальна
        bx = px + dx * 12
        return f'<line x1="{bx}" y1="{py - 7}" x2="{bx}" y2="{py + 7}" stroke="#000" stroke-width="1.0"/>'
    by = py + dy * 12
    return f'<line x1="{px - 7}" y1="{by}" x2="{px + 7}" y2="{by}" stroke="#000" stroke-width="1.0"/>'


def crow_many(px: float, py: float, dx: int, dy: int) -> str:
    """Метка «N» — три «лапки», вершина на краю таблицы, веер НАРУЖУ.

    (dx, dy) — направление НАРУЖУ от края таблицы (туда же уходит линия)."""
    L = 13
    if dx != 0:  # веер по горизонтали наружу
        ex = px + dx * L
        return (f'<line x1="{px}" y1="{py}" x2="{ex}" y2="{py - 8}" stroke="#000" stroke-width="0.9"/>'
                f'<line x1="{px}" y1="{py}" x2="{ex}" y2="{py}" stroke="#000" stroke-width="0.9"/>'
                f'<line x1="{px}" y1="{py}" x2="{ex}" y2="{py + 8}" stroke="#000" stroke-width="0.9"/>')
    ey = py + dy * L
    return (f'<line x1="{px}" y1="{py}" x2="{px - 8}" y2="{ey}" stroke="#000" stroke-width="0.9"/>'
            f'<line x1="{px}" y1="{py}" x2="{px}" y2="{ey}" stroke="#000" stroke-width="0.9"/>'
            f'<line x1="{px}" y1="{py}" x2="{px + 8}" y2="{ey}" stroke="#000" stroke-width="0.9"/>')


def poly(points: list[tuple[float, float]]) -> str:
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{pts}" stroke="#000" fill="none" stroke-width="0.9"/>'


# ---- данные таблиц ------------------------------------------------------------
admins = [
    ('admin_id', 'varchar(32)', 'PK'),
    ('email', 'varchar(254)', 'UQ, NN'),
    ('password', 'varchar(256)', 'NN'),
    ('full_name', 'varchar(254)', 'NULL'),
    ('enrollment_token', 'varchar(64)', 'UQ, NN'),
    ('created_at', 'timestamptz', 'NN'),
    ('updated_at', 'timestamptz', 'NN'),
]
operators = [
    ('operator_id', 'varchar(32)', 'PK'),
    ('admin_id', 'varchar(32)', 'FK, NN'),
    ('username', 'varchar(64)', 'UQ, NN'),
    ('password', 'varchar(256)', 'NN'),
    ('full_name', 'varchar(254)', 'NN'),
    ('passport', 'varchar(32)', 'NN'),
    ('address', 'varchar(512)', 'NN'),
    ('is_active', 'bool', 'NN'),
    ('created_at', 'timestamptz', 'NN'),
    ('updated_at', 'timestamptz', 'NN'),
]
drones = [
    ('drone_id', 'varchar(64)', 'PK'),
    ('admin_id', 'varchar(32)', 'FK, NN'),
    ('drone_token', 'varchar(64)', 'UQ, NN'),
    ('name', 'varchar(64)', 'NULL'),
    ('enrolled_at', 'timestamptz', 'NULL'),
    ('created_at', 'timestamptz', 'NN'),
    ('last_seen_at', 'timestamptz', 'NULL'),
]
deliveries = [
    ('delivery_id', 'varchar(32)', 'PK'),
    ('admin_id', 'varchar(32)', 'FK, NN'),
    ('drone_id', 'varchar(64)', 'FK, NULL'),
    ('operator_id', 'varchar(32)', 'FK, NULL'),
    ('drone_name', 'varchar(64)', 'NULL'),
    ('operator_name', 'varchar(254)', 'NULL'),
    ('operator_passport', 'varchar(32)', 'NULL'),
    ('status', 'varchar(16)', 'NN'),
    ('departure_address', 'varchar(512)', 'NULL'),
    ('departure_lat', 'float', 'NULL'),
    ('departure_lon', 'float', 'NULL'),
    ('destination_address', 'varchar(512)', 'NULL'),
    ('destination_lat', 'float', 'NULL'),
    ('destination_lon', 'float', 'NULL'),
    ('cargo_description', 'varchar(512)', 'NULL'),
    ('created_at', 'timestamptz', 'NN'),
    ('accepted_at', 'timestamptz', 'NULL'),
    ('delivered_at', 'timestamptz', 'NULL'),
    ('cancelled_at', 'timestamptz', 'NULL'),
]

# ---- раскладка ----------------------------------------------------------------
W, H = 1260, 1020
body = []
t_op, g_op = table(30, 70, 'operators', operators)
t_ad, g_ad = table(445, 70, 'admins', admins)
t_dr, g_dr = table(855, 70, 'drones', drones)
t_de, g_de = table(445, 470, 'deliveries', deliveries)
body += [t_op, t_ad, t_dr, t_de]

rels = []
# admins(1) — operators(N): горизонталь в верхней полосе
y1 = g_ad.top + 60
rels.append(poly([(g_ad.left, y1), (g_op.right, y1)]))
rels.append(crow_one(g_ad.left, y1, -1, 0))   # наружу влево от admins
rels.append(crow_many(g_op.right, y1, 1, 0))  # наружу вправо от operators
# admins(1) — drones(N): горизонталь
y2 = g_ad.top + 60
rels.append(poly([(g_ad.right, y2), (g_dr.left, y2)]))
rels.append(crow_one(g_ad.right, y2, 1, 0))    # наружу вправо от admins
rels.append(crow_many(g_dr.left, y2, -1, 0))   # наружу влево от drones
# admins(1) — deliveries(N): вертикаль вниз по центру
xv = g_ad.cx
rels.append(poly([(xv, g_ad.bottom), (xv, g_de.top)]))
rels.append(crow_one(xv, g_ad.bottom, 0, 1))   # наружу вниз от admins
rels.append(crow_many(xv, g_de.top, 0, -1))    # наружу вверх от deliveries
# drones(1) — deliveries(N): вниз и влево к правому краю deliveries
yj = 415
rels.append(poly([(g_dr.cx, g_dr.bottom), (g_dr.cx, yj), (g_de.right + 75, yj), (g_de.right + 75, g_de.top + 70), (g_de.right, g_de.top + 70)]))
rels.append(crow_one(g_dr.cx, g_dr.bottom, 0, 1))      # наружу вниз от drones
rels.append(crow_many(g_de.right, g_de.top + 70, 1, 0))  # наружу вправо от deliveries
# operators(1) — deliveries(N): вниз и вправо к левому краю deliveries
rels.append(poly([(g_op.cx, g_op.bottom), (g_op.cx, yj + 30), (g_de.left - 75, yj + 30), (g_de.left - 75, g_de.top + 130), (g_de.left, g_de.top + 130)]))
rels.append(crow_one(g_op.cx, g_op.bottom, 0, 1))        # наружу вниз от operators
rels.append(crow_many(g_de.left, g_de.top + 130, -1, 0))  # наружу влево от deliveries

caption = (f'<text x="{W/2}" y="{H-22}" text-anchor="middle" font-style="italic" '
           f'font-size="17">Рисунок 1 – Логическая модель данных (ER-диаграмма) системы Mavix</text>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="Liberation Serif, Times New Roman, serif">\n'
       f'<rect width="{W}" height="{H}" fill="#fff"/>\n'
       + '\n'.join(rels) + '\n' + '\n'.join(body) + '\n' + caption + '\n</svg>\n')

if __name__ == '__main__':
    import pathlib
    out = pathlib.Path(__file__).parent / 'er_model.svg'
    out.write_text(svg, encoding='utf-8')
    print(out)
