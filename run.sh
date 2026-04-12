#!/bin/bash
echo "[VirtuNet] Running VirtuNet."
cd "$(dirname "$0")"
sudo PYWEBVIEW_GUI=qt .venv/bin/python main.py