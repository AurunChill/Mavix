# Сборка MavixDesktop под Windows (.exe). Запускать на Windows-машине в PowerShell.
# Требуется Python 3.12 (с галкой "Add Python to PATH"). Если pip ругнётся на
# "Microsoft Visual C++ 14.0 required" — поставить Microsoft C++ Build Tools
# (Desktop development with C++).
#
# Сервер собрать .exe сам не может (нужна Windows). Соберите здесь и отправьте
# файл dist\mavixdesktop.exe — затем на сервере положите его в prebuilt и
# перезапустите контейнер app (см. build_desktop_linux.sh / BUILD.md).

$ErrorActionPreference = "Stop"

# git clone https://github.com/dexstronggg/MavixDesktop-UI ; cd MavixDesktop-UI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install pyinstaller
pyinstaller mavixdesktop.spec        # результат: dist\mavixdesktop.exe

Write-Host "Готово: dist\mavixdesktop.exe"
Write-Host "Отправьте его на сервер, напр.:"
Write-Host '  scp dist\mavixdesktop.exe root@SERVER_IP:/srv/mavix/MavixServer/prebuilt/'
Write-Host '  ssh root@SERVER_IP "cd /srv/mavix && docker compose restart app"'
