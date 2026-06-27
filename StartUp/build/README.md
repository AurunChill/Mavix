# StartUp/build — сборка и отправка на сервер

Скрипты для сборки дистрибутивов и деплоя. **Сначала задайте параметры в
[`config.sh`](config.sh)** (как минимум `SERVER_IP`).

| Скрипт | Что делает | Где запускать |
|---|---|---|
| `config.sh` | Общие параметры (IP сервера, пути, пользователь) | — (подключается остальными) |
| `build_board_wheels.sh` | Собрать wheels борта (MavixBoard) и отправить на сервер | машина с архитектурой борта (обычно RPi/aarch64) |
| `build_desktop_linux.sh` | Собрать Linux-бинарь MavixDesktop (PyInstaller), отправить, перезапустить `app` | Linux (Ubuntu 22.04/24.04) |
| `build_desktop_windows.ps1` | Собрать `.exe` MavixDesktop | Windows + Python 3.12 (PowerShell) |
| `deploy_server.sh` | `git pull` + `docker compose up -d --build` на VPS | любая машина с SSH к серверу |

Порядок типового релиза:
1. `deploy_server.sh` — выкатить серверную часть.
2. `build_board_wheels.sh` — обновить дистрибутив борта (если менялся MavixBoard).
3. `build_desktop_linux.sh` / `build_desktop_windows.ps1` — обновить приложение
   оператора (если менялся MavixDesktop).

Ручные команды сборки каждого компонента — в его репозитории:
`MavixDesktop-UI/scripts/` (`build_binary.sh` — Linux-бинарь, `build_windows.ps1`
— `.exe`); сборка wheels борта (в т.ч. без RPi через QEMU) — `MavixServer/scripts/README.md`.
