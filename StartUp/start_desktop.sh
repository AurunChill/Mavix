#!/bin/bash
set -e
cd "$(dirname "$0")/../MavixDesktop-UI"
source .venv/bin/activate
python -m mavixdesktop
