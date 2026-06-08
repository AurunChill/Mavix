На RPi4 (он у тебя aarch64 — нужны wheels именно под эту архитектуру):


# 1. Зависимости (один раз)
sudo apt update && sudo apt install -y git python3 python3-pip python3-venv

# 2. Склонить ОБА репа — для wheels нужны и MavixBoard (исходник),
#    и MavixServer (там скрипт build_wheels.sh)
git clone https://github.com/AurunChill/MavixBoard
git clone https://github.com/AurunChill/MavixServer

# 3. Собрать wheels (~5-15 минут на RPi)
cd MavixServer
./scripts/build_wheels.sh ../MavixBoard
ls wheels/board/   # *.whl на ~15 МБ суммарно
Передать на VPS:


# с RPi
scp -r wheels/board/* root@85.198.102.188:/srv/mavix/MavixServer/wheels/board/
На VPS — ничего перезапускать не надо. Кэш .tar.gz инвалидируется автоматически: следующее скачивание увидит, что хеш wheels изменился, и пересоберёт.

.env на RPi для этого шага не нужен — .env нужен только если ты хочешь запустить board из исходников для отладки. Для сборки wheels — нет.

Хорошо, как сбилдить AppImage для mavixdesktop?
На твоей Linux-машине (x86_64):


cd ~/Projects/Mavix/MavixDesktop-UI
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pyinstaller
./scripts/build_binary.sh
Результат: dist/mavixdesktop-linux (~150 МБ).

Отправка на сервер:


scp dist/mavixdesktop-linux root@85.198.102.188:/srv/mavix/MavixServer/prebuilt/
ssh root@85.198.102.188 'cd /srv/mavix && docker compose restart app'
После этого кнопка «Linux (.AppImage)» на сайте отдаёт его как mavixdesktop-linux.AppImage.

Заметки:

venv нужен один раз; следующие билды — просто source .venv/bin/activate && ./scripts/build_binary.sh.
Если pip ругается на отсутствие dev-пакетов (e.g. qt6-base-dev, libgl1) — sudo apt install libgl1 libegl1 libxkbcommon0.
Бинарь зависит от glibc хоста сборки. Безопаснее билдить на относительно старом Linux (Ubuntu 22.04/24.04 норм).
И как на .exe
Сам не соберёшь — нужна Windows-машина. Отдай этому человеку 4 команды:


git clone https://github.com/dexstronggg/MavixDesktop-UI
cd MavixDesktop-UI
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -e . ; pip install pyinstaller ; pyinstaller mavixdesktop.spec
Результат: dist\mavixdesktop.exe. Пусть пришлёт.

Что ему нужно перед этим:

Python 3.12 с https://python.org (галка «Add Python to PATH» при установке).
Если pip ругнётся на «Microsoft Visual C++ 14.0 required» — поставить Microsoft C++ Build Tools с https://visualstudio.microsoft.com/visual-cpp-build-tools/ (включить «Desktop development with C++»).
Доступ к репозиторию (приватный) — твой PAT или добавить его в коллабораторы.
У тебя дальше:


scp mavixdesktop.exe root@85.198.102.188:/srv/mavix/MavixServer/prebuilt/
ssh root@85.198.102.188 'cd /srv/mavix && docker compose restart app'
Кнопка «Windows (.exe)» на сайте начнёт его отдавать.