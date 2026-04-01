#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root."
    exit 1
fi

INSTALL_DIR="/opt/virtunet"
VENV="$INSTALL_DIR/.venv"

mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR"

python3.13 -m venv "$VENV"
"$VENV/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

cat > /usr/local/bin/virtunet << 'EOF'
#!/bin/bash
cd /opt/virtunet
sudo PYWEBVIEW_GUI=qt /opt/virtunet/.venv/bin/python main.py
EOF
chmod +x /usr/local/bin/virtunet

echo "Installed. Run: sudo virtunet"