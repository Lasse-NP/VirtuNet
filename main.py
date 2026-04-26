import setup
import os
import argparse
import asyncio
import sys
import signal

async def on_shutdown():
    await asyncio.to_thread(run_cleanup)

def handle_signal(sig, frame):
    run_cleanup()
    sys.exit(1)

def cli_quickstart(preset_name: str):
    from Logic.Presets import PRESET_CONFIGS
    from GUI.SessionSetting import build_host_list, session_rows, vendor_dictionary
    from Networking.OpenVPN.server import openvpn_server
    from Networking.MiniNet.mininet import mininet_network
    from Networking.OpenVPN.network import get_local_ip
    from Service.ConnectionHandler import start_join_server

    if preset_name not in PRESET_CONFIGS:
        print(f"Unknown preset '{preset_name}'. Available: {', '.join(PRESET_CONFIGS)}")
        sys.exit(1)

    session_rows.clear()
    for row in PRESET_CONFIGS[preset_name]:
        session_rows.append({
            'count': row['count'],
            'vendor_name': row['vendor_name'],
            'device_class': next(
                cls for cls in vendor_dictionary[row['vendor_name']].__subclasses__()
                if cls.__name__ == row['device_class'].__name__.split('.')[-1]
            )
        })

    host_list = build_host_list()
    print(f"[VirtuNet] Quickstart: {preset_name} - {len(host_list)} device(s)")

    print("[VirtuNet] Initializing OpenVPN...")
    openvpn_server.initialize()

    print("[VirtuNet] Configuring Mininet...")
    mininet_network.configuration(host_list)

    start_join_server()
    get_local_ip()

    print("=" * 40)
    print("Devices:")
    for host, device in mininet_network.get_hosts().items():
        print(f"{device.name}: {host.IP()}")
    print("=" * 40)

    print("[VirtuNet] Network up. Ctrl+C to stop.")
    try:
        signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        run_cleanup()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--preset', metavar='NAME')
    parser.add_argument('--list-presets', action='store_true')
    args, _ = parser.parse_known_args()

    if args.list_presets:
        from Logic.Presets import PRESET_CONFIGS
        print("Available presets:", ', '.join(PRESET_CONFIGS))
        sys.exit(0)

    setup.ensure_root()
    setup.check_dependencies()

    from Networking.cleanup import run_cleanup
    from Networking.MiniNet.mdns import setup_avahi

    setup_avahi()
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    if args.preset:
        cli_quickstart(args.preset)
        sys.exit(0)

    from nicegui import ui, app
    import GUI.Frontpage
    import GUI.SessionSetting
    import GUI.CustomSetup
    import GUI.Lobby
    import GUI.ControlCenter
    import GUI.AfterActionReport

    os.environ['PYWEBVIEW_GUI'] = 'qt'
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--no-sandbox'
    print(f'*** PYTHON_PATH: {sys.executable}')
    app.on_shutdown(on_shutdown)
    app.native.window_args['min_size'] = (550, 1000)
    app.native.start_args['icon'] = 'GUI/Assets/VirtuNetIcon.png'
    ui.run(native=True, reload=False, window_size=(1000, 1000), title='VirtuNet', storage_secret='my-super-secret-key-123')
    run_cleanup()