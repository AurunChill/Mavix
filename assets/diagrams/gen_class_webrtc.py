#!/usr/bin/env python3
"""UML Class — WebRTC-слой MavixBoard (runtime-классы и их композиция)."""
from __future__ import annotations

import pathlib
import types

from diagramlib import Canvas

NAME_H = 28
ROW_H = 20


def uml_class(c: Canvas, x, y, w, name, attrs, methods):
    h = NAME_H + ROW_H * (len(attrs) + len(methods))
    c.rect(x, y, w, h, sw=1.2)
    c.text(x + w / 2, y + 19, name, fs=16, bold=True)
    c.line(x, y + NAME_H, x + w, y + NAME_H, sw=1.0)
    ry = y + NAME_H
    for a in attrs:
        c.text(x + 9, ry + 14, a, fs=12.5, anchor='start')
        ry += ROW_H
    c.line(x, ry, x + w, ry, sw=1.0)
    for m in methods:
        c.text(x + 9, ry + 14, m, fs=12.5, anchor='start')
        ry += ROW_H
    return types.SimpleNamespace(x=x, y=y, w=w, h=h, cx=x + w / 2, cy=y + h / 2,
                                 left=x, right=x + w, top=y, bottom=y + h)


def diamond(c, px, py, dx, dy):
    s = 9
    if dx != 0:
        pts = [(px, py - s), (px + dx * s, py), (px + dx * 2 * s, py), (px + dx * s, py + s)]
    else:
        pts = [(px - s, py), (px, py + dy * s), (px, py + dy * 2 * s), (px + s, py + dy * s)]
    c.add(f'<polygon points="{" ".join(f"{a:.0f},{b:.0f}" for a,b in pts)}" fill="#000" stroke="#000"/>')


c = Canvas(1560, 1080)

g_fc = uml_class(c, 100, 130, 340, 'FCService', [
    '+ kind: str', '+ name: str', '+ is_connected: bool'],
    ['+ start() / stop()', '+ send(data)', '+ set_telemetry_callback(cb)', '+ set_packet_callback(cb)'])
g_co = uml_class(c, 560, 90, 410, 'SessionCoordinator', [
    '- _signal_client', '- _manager: WebRTCManager', '- _pipeline: GStreamerPipe', '- _fc_service: FCService'],
    ['+ run() / stop()', '- _on_message(msg)', '- _handle_connect(gcs_id)', '- _teardown()', '- _release_pipeline(p)'])
g_gp = uml_class(c, 1120, 130, 340, 'GStreamerPipe', [
    '+ pipeline', '+ webrtc_elem', '+ cameras'],
    ['+ start() / stop()', '+ update_bitrate(i, kbps)', '- _disable_upnp(el)'])
g_mg = uml_class(c, 585, 470, 380, 'WebRTCManager', [
    '- _peer: PeerSession', '- _channels: DataChannelHub', '- _webrtc'],
    ['+ start_session(gcs_id)', '+ end_session()', '+ handle_sdp() / handle_ice()', '+ notify_fc_changed()'])
g_pe = uml_class(c, 140, 800, 360, 'PeerSession', [
    '+ gcs_id: str', '+ offer_sdp: str', '- _webrtc (из GStreamerPipe)'],
    ['+ apply_answer(sdp)', '+ add_remote_ice(cand)', '+ close()'])
g_dc = uml_class(c, 1040, 800, 380, 'DataChannelHub', [
    '+ packet · ping', '+ config · telemetry'],
    ['+ close()'])

# --- связи --------------------------------------------------------------------
# Coord ◆— Manager
c.poly([(g_co.cx, g_co.bottom), (g_co.cx, g_mg.top)], marker='arr')
diamond(c, g_co.cx, g_co.bottom, 0, 1)
# Coord ◆— GStreamerPipe
c.poly([(g_co.right, 175), (g_gp.left, 175)], marker='arr')
diamond(c, g_co.right, 175, 1, 0)
# Coord —> FCService (внедрён)
c.poly([(g_co.left, 200), (g_fc.right, 200)], marker='arr')
c.text((g_co.left + g_fc.right) / 2, 192, 'fc_service', fs=12)
# Manager ◆— PeerSession
c.poly([(g_mg.left + 60, g_mg.bottom), (g_mg.left + 60, 760), (g_pe.cx, 760), (g_pe.cx, g_pe.top)], marker='arr')
diamond(c, g_mg.left + 60, g_mg.bottom, 0, 1)
# Manager ◆— DataChannelHub
c.poly([(g_mg.right - 60, g_mg.bottom), (g_mg.right - 60, 760), (g_dc.cx, 760), (g_dc.cx, g_dc.top)], marker='arr')
diamond(c, g_mg.right - 60, g_mg.bottom, 0, 1)

out = pathlib.Path(__file__).parent / 'class_webrtc.svg'
out.write_text(c.svg('Рисунок 8 – Диаграмма классов WebRTC-слоя MavixBoard'), encoding='utf-8')
print(out)
