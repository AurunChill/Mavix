#!/usr/bin/env python3
"""C4 уровень 3 — компоненты контейнера MavixServer."""
from __future__ import annotations

import pathlib

from diagramlib import Canvas

c = Canvas(1500, 1060)

# Граница контейнера
c.rect(110, 90, 1290, 770, sw=1.6)
c.text(140, 122, 'MavixServer  [Python, FastAPI, SQLAlchemy, Docker]', fs=16, anchor='start', bold=True)

# Компоненты (имя + состав)
c.box_multi(180, 160, 380, 110, ['API-роутеры (FastAPI)', 'auth · operators · deliveries', 'drones · builds · ice'])
c.box_multi(610, 160, 210, 110, ['Core', 'безопасность (JWT)', 'email · config'])
c.box_multi(870, 160, 430, 110, ['WS-сигналинг', 'gcs · admin · drone handlers', 'relay · notifier · registry'])
c.box_multi(440, 360, 520, 100, ['Сервисы (бизнес-логика)', 'admin · operator · delivery · drone · build'])
c.box_multi(480, 510, 440, 95, ['Репозитории', 'admin · operator · delivery · drone'])
c.box_multi(510, 650, 380, 90, ['Модели (SQLAlchemy ORM)', 'Admin · Operator · Drone · Delivery'])

# Внешняя СУБД
c.box(560, 905, 300, 80, 'PostgreSQL', '(контейнер БД)', sw=1.2, title_fs=16)

# --- связи --------------------------------------------------------------------
# API -> Core, WS -> Core (JWT)
c.poly([(560, 210), (610, 210)], marker='arr')
c.text(585, 200, 'JWT', fs=13)
c.poly([(870, 210), (820, 210)], marker='arr')
c.text(845, 200, 'JWT', fs=13)
# API -> Services
c.poly([(370, 270), (370, 405), (440, 405)], marker='arr')
c.text(372, 330, 'вызов сервисов', fs=13, anchor='start')
# WS -> Services
c.poly([(1085, 270), (1085, 405), (960, 405)], marker='arr')
c.text(1080, 330, 'сценарии заявок / сессий', fs=13, anchor='end')
# Services -> Repositories
c.poly([(700, 460), (700, 510)], marker='arr')
c.text(712, 492, 'запросы', fs=13, anchor='start')
# Repositories -> Models
c.poly([(700, 605), (700, 650)], marker='arr')
c.text(712, 635, 'ORM-объекты', fs=13, anchor='start')
# Models -> PostgreSQL
c.poly([(700, 740), (700, 905)], marker='arr')
c.text(712, 830, 'SQL (asyncpg)', fs=13, anchor='start')

out = pathlib.Path(__file__).parent / 'c4_component_server.svg'
out.write_text(c.svg('Рисунок 4 – Диаграмма компонентов (C4 Level 3) контейнера MavixServer'), encoding='utf-8')
print(out)
