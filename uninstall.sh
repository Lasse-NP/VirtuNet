#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root."
    exit 1
fi

INSTALL_DIR="/opt/virtunet"

if [ -f "$INSTALL_DIR/main.py" ]; then
    echo "*** Running session cleanup..."
    "$INSTALL_DIR/.venv/bin/python" -c "
from Networking.cleanup import run_cleanup
run_cleanup()
" 2>/dev/null || true
fi

rm -rf "$INSTALL_DIR"
rm -f /usr/local/bin/virtunet

rm -rf /var/lib/virtunet

echo "VirtuNet uninstalled successfully."