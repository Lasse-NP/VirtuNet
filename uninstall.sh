#!/bin/bash
set -e

INSTALL_DIR="/opt/virtunet"

if [ "$EUID" -ne 0 ]; then
    echo "[VirtuNet] Please run as Root via sudo."
    exit 1
fi

if [ ! -d "$INSTALL_DIR" ]; then
    echo "[VirtuNet] VirtuNet is not installed."
    exit 1
fi

if pgrep -f "/opt/virtunet/.venv/bin/python main.py" > /dev/null 2>&1; then
  echo "[VirtuNet] Stopping Running VirtuNet Processes."
  pkill -f "/opt/virtunet/.venv/bin/python main.py" 2>/dev/null || true
  sleep 3
fi

echo "[VirtuNet] Cleaning Up VirtuNet."
if [ -f "$INSTALL_DIR/main.py" ]; then
    echo "*** Running session cleanup..."
    "$INSTALL_DIR/.venv/bin/python" -c "
from Networking.cleanup import run_cleanup
run_cleanup()
" 2>/dev/null || true
fi

echo "[VirtuNet] Removing Installation."
rm -rf "$INSTALL_DIR"
echo "[VirtuNet] Removing VirtuNet from Path."
rm -f /usr/local/bin/virtunet
echo "[VirtuNet] Removing Orphaned VirtuNet Configs."
rm -rf /var/lib/virtunet

echo "[VirtuNet] Uninstalled Successfully."