cd "$(dirname "$0")"
sudo --preserve-env=DISPLAY,WAYLAND_DISPLAY,XDG_RUNTIME_DIR,XAUTHORITY,DBUS_SESSION_BUS_ADDRESS \
    .venv/bin/python main.py