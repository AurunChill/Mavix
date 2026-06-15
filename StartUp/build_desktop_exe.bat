@echo off
REM Сборка Windows .exe MavixDesktop (PyInstaller).
REM ЗАПУСКАТЬ НА WINDOWS: двойной клик или из CMD / PowerShell.
REM Требования: Python 3.12 с галкой "Add Python to PATH".
REM Если pip ругнётся "Microsoft Visual C++ 14.0 required" —
REM поставить Microsoft C++ Build Tools.

set SERVER_IP=85.198.102.188

cd /d "%~dp0..\MavixDesktop-UI"

python -m venv .venv
call .venv\Scripts\activate.bat
pip install -e .
pip install pyinstaller
pyinstaller mavixdesktop.spec

echo.
echo ==^> Готово. Бинарь: %CD%\dist\mavixdesktop.exe
echo ==^> Перенести на сервер:
echo     scp dist\mavixdesktop.exe root@%SERVER_IP%:/srv/mavix/MavixServer/prebuilt/
