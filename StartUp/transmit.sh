#!/bin/bash
rsync -av --exclude='.venv' --exclude='__pycache__' ./MavixBoard/src/ rpi@10.88.250.216:/home/rpi/MavixNew/src/
