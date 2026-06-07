#!/bin/bash
set -e
cd "$(dirname "$0")/../MavixServer"
docker compose up db -d
echo "Postgres запущен на localhost:5432"
