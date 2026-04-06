#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root."
    exit 1
fi

if ! command -v python3.13 &>/dev/null; then
    echo "Python 3.13 is required. Please install it and run this script again."
    exit 1
fi

INSTALL_DIR="/opt/virtunet"
VENV="$INSTALL_DIR/.venv"

source /etc/os-release
FAMILY=""
for ID_CHECK in $ID $ID_LIKE; do
    case "$ID_CHECK" in
        ubuntu|debian)        FAMILY="debian" ;;
        arch|manjaro|cachyos) FAMILY="arch" ;;
        fedora|rhel|centos)   FAMILY="fedora" ;;
        opensuse*)            FAMILY="opensuse" ;;
    esac
    [ -n "$FAMILY" ] && break
done

case "$FAMILY" in
    debian)
        apt-get install -y build-essential libnetfilter-queue-dev python3.13-dev libxcb-cursor0
        ;;
    arch)
        pacman -S --noconfirm --needed base-devel libnetfilter_queue xcb-util-cursor
        ;;
    fedora)
        dnf install -y gcc libnetfilter_queue-devel python3-devel xcb-util-cursor
        ;;
    opensuse)
        zypper install -y gcc libnetfilter_queue-devel python313-devel xcb-util-cursor
        ;;
    *)
        echo "WARNING: Unknown distro, skipping build dependency install. netfilterqueue may fail to build."
        ;;
esac

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