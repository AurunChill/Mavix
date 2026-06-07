#!/bin/bash
set -e
cd "$(dirname "$0")/../MavixBoard"
source .venv/bin/activate
python -m mavixboard
