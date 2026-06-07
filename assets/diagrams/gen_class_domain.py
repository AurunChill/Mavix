#!/usr/bin/env python3
"""UML Class — доменная модель MavixServer (сущности SQLAlchemy + enum)."""
from __future__ import annotations

import pathlib
import types

from diagramlib import Canvas

NAME_H = 30
ROW_H = 21


def uml_class(c: Canvas, x, y, w, name, attrs, stereo=None):
    nh = NAME_H + (16 if stereo else 0)
    h = nh + ROW_H * len(attrs)
    c.rect(x, y, w, h, sw=1.2)
    if stereo:
        c.text(x + w / 2, y + 16, f'«{stereo}»', fs=12, italic=True)
        c.text(x + w / 2, y + 33, name, fs=16, bold=True)
    else:
        c.text(x + w / 2, y + 20, name, fs=16, bold=True)
    c.line(x, y + nh, x + w, y + nh, sw=1.0)
    ry = y + nh
    for a in attrs:
        c.text(x + 9, ry + 15, a, fs=13, anchor='start')
        ry += ROW_H
    return types.SimpleNamespace(x=x, y=y, w=w, h=h, cx=x + w / 2, cy=y + h / 2,
                                 left=x, right=x + w, top=y, bottom=y + h)


def diamond(c: Canvas, px, py, dx, dy):
    """Закрашенный ромб композиции у «целого» (наружу по (dx,dy))."""
    s = 9
    if dx != 0:
        a, b, d, e = (px, py - s), (px + dx * s, py), (px + dx * 2 * s, py), (px + dx * s, py + s)
    else:
        a, b, d, e = (px - s, py), (px, py + dy * s), (px, py + dy * 2 * s), (px + s, py + dy * s)
    pts = ' '.join(f'{p[0]:.0f},{p[1]:.0f}' for p in (a, b, d, e))
    c.add(f'<polygon points="{pts}" fill="#000" stroke="#000"/>')


c = Canvas(1520, 1060)

g_ad = uml_class(c, 590, 90, 340, 'Admin', [
    '+ admin_id: str «PK»', '+ email: str «unique»', '+ password: str',
    '+ full_name: str | None', '+ enrollment_token: str «unique»', '+ created_at: datetime'], 'entity')
g_op = uml_class(c, 110, 470, 330, 'Operator', [
    '+ operator_id: str «PK»', '+ admin_id: str «FK»', '+ username: str «unique»',
    '+ full_name: str', '+ passport: str', '+ address: str', '+ is_active: bool'], 'entity')
g_dr = uml_class(c, 1080, 470, 330, 'Drone', [
    '+ drone_id: str «PK»', '+ admin_id: str «FK»', '+ drone_token: str «unique»',
    '+ name: str | None', '+ enrolled_at: datetime | None'], 'entity')
g_de = uml_class(c, 560, 560, 400, 'Delivery', [
    '+ delivery_id: str «PK»', '+ status: str', '+ drone_id: str | None «FK»',
    '+ operator_id: str | None «FK»', '+ destination_lat/lon: float', '+ drone_name: str | None ⟨снимок⟩',
    '+ operator_name: str | None ⟨снимок⟩', '+ created_at / accepted_at: datetime'], 'entity')
g_st = uml_class(c, 1090, 840, 320, 'DeliveryStatus', [
    'OFFERED', 'ACCEPTED', 'IN_FLIGHT', 'DELIVERED', 'CANCELLED'], 'enumeration')

# --- композиции Admin ◆—> (cascade delete) ------------------------------------
# Admin -> Operator
c.poly([(g_ad.left, 150), (350, 150), (350, g_op.top)], marker='arr')
diamond(c, g_ad.left, 150, -1, 0)
c.text(360, 142, '1', fs=12, anchor='start')
c.text(335, g_op.top - 8, '1..*', fs=12, anchor='end')
# Admin -> Drone
c.poly([(g_ad.right, 150), (1245, 150), (1245, g_dr.top)], marker='arr')
diamond(c, g_ad.right, 150, 1, 0)
c.text(1160, 142, '1', fs=12, anchor='end')
c.text(1255, g_dr.top - 8, '1..*', fs=12, anchor='start')
# Admin -> Delivery
c.poly([(g_ad.cx, g_ad.bottom), (g_ad.cx, g_de.top)], marker='arr')
diamond(c, g_ad.cx, g_ad.bottom, 0, 1)
c.text(g_ad.cx + 10, g_ad.bottom + 26, '1', fs=12, anchor='start')
c.text(g_ad.cx + 10, g_de.top - 8, '1..*', fs=12, anchor='start')
# --- ассоциации (SET NULL) ----------------------------------------------------
# Operator -> Delivery
c.poly([(g_op.right, 660), (g_de.left, 660)], marker='arr')
c.text(g_op.right + 8, 652, '1', fs=12, anchor='start')
c.text(g_de.left - 8, 652, '0..*', fs=12, anchor='end')
# Drone -> Delivery
c.poly([(g_dr.left, 640), (g_de.right, 640)], marker='arr')
c.text(g_dr.left - 8, 632, '1', fs=12, anchor='end')
c.text(g_de.right + 8, 632, '0..*', fs=12, anchor='start')
# Delivery ··> DeliveryStatus (зависимость)
c.poly([(g_de.right, 760), (g_st.left, 760), (g_st.left, g_st.cy)], marker='open', dash=True)
c.text((g_de.right + g_st.left) / 2, 752, '«использует»', fs=12)

out = pathlib.Path(__file__).parent / 'class_domain.svg'
out.write_text(c.svg('Рисунок 7 – Диаграмма классов доменной модели MavixServer'), encoding='utf-8')
print(out)
