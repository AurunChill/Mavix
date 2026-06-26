#!/bin/bash
# Сборка Windows .exe MavixDesktop (PyInstaller).
# ЗАПУСКАТЬ НА WINDOWS в Git Bash, с установленным Python 3.12
# (галка "Add Python to PATH"). Если pip ругнётся на "Microsoft Visual C++
# 14.0 required" — поставить Microsoft C++ Build Tools.
set -e
SERVER_IP="85.198.69.77"        # подставь свой IP/домен сервера
cd "$(dirname "$0")/../MavixDesktop-UI"
python -m venv .venv
source .venv/Scripts/activate     # путь venv в Windows (Git Bash)
pip install -e .
pip install pyinstaller
pyinstaller mavixdesktop.spec
echo
echo "==> Готово. Бинарь: $(pwd)/dist/mavixdesktop.exe"
echo "==> Перенести на сервер:"
echo "    scp dist/mavixdesktop.exe root@${SERVER_IP}:/srv/mavix/MavixServer/prebuilt/"
