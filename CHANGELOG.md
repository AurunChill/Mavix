# Changelog

Все значимые изменения проекта **Mavix** (аппаратно-программный комплекс доставки
грузов на базе БПЛА) документируются в этом файле. Проект объединяет бортовой
модуль (MavixBoard), станцию оператора (MavixDesktop-UI) и взаимодействует с
информационной системой (MavixServer, MavixWeb) по REST и WebSocket-сигналингу.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
проект придерживается [семантического версионирования](https://semver.org/lang/ru/).

## [1.0.0] - 2026-06-08

Первый стабильный релиз комплекса доставки грузов на базе БПЛА.

### Added
- Полная ГОСТ-документация всех компонентов и диаграммы по репозиториям.
- UML Activity (диаграмма деятельности), развёрнутый `ForServer/Main/README`.
- Инфраструктура развёртывания: docker-compose, скрипты сборки и деплоя.
- Проприетарная лицензия (LICENSE) и история изменений (CHANGELOG).

### Security
- Секреты в `ForServer` заменены на заглушки (вынесены из репозитория).

## [0.8.0] - 2026-06-07

### Added
- Полный комплект диаграмм для ВКР: ER-модель БД, C4 (Context/Container/Component),
  UML Class (доменная модель и WebRTC-слой), UML Sequence (приём заявки, WebRTC),
  Use Case, Deployment, IDEF0 (SADT) и DFD (Гейн–Сарсон).
- Тулинг генерации диаграмм: `diagramlib`, рендер SVG→PNG, `RULES.md`, `PROMPT.md`.
- Корневой README (обзор проекта и ссылки), `StartUp/build` — скрипты сборки и деплоя.
- `PRINCIPLES.md` — SOLID/DRY/KISS/YAGNI на реальном коде проекта.

## [0.5.0] - 2026-06-06

### Changed
- Переориентация комплекса с FPV-управления на систему доставки грузов —
  все четыре репозитория переведены на доставку, тесты зелёные.

### Added
- Оформление компонентов как git-сабмодулей и руководство по развёртыванию.

## [0.1.0] - 2026-05-28

### Added
- Начальная интеграция проекта Mavix (прототип дистанционного управления).

[1.0.0]: https://github.com/AurunChill/Mavix/releases/tag/v1.0.0
[0.8.0]: https://github.com/AurunChill/Mavix/compare/v0.5.0...v0.8.0
[0.5.0]: https://github.com/AurunChill/Mavix/compare/v0.1.0...v0.5.0
[0.1.0]: https://github.com/AurunChill/Mavix/releases/tag/v0.1.0
