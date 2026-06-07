#!/bin/bash
set -e
cd "$(dirname "$0")/../MavixServer"
source .venv/bin/activate
alembic upgrade head
uvicorn mavixserver.__main__:app --host 0.0.0.0 --port 8000 --reload
