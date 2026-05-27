import setup
import os
import argparse
import asyncio
import sys
import signal

async def on_shutdown():
    # Run the blocking cleanup function in a thread so it doesn't stall the NiceGUI event loop.
    await asyncio.to_thread(run_cleanup)

def handle_signal(sig, frame):
    # Called by SIGTERM or SIGINT; run cleanup synchronously then exit with a non-zero code.
    run_cleanup()
    sys.exit(1)

def cli_quickstart(preset_name: str):
    # Import here to avoid pulling in GUI and networking modules before root/dependency checks pass.
    from Logic.Presets import PRESET_CONFIGS
    from GUI.SessionSetting import build_host_list, session_rows, vendor_dictionary
    from Networking.OpenVPN.server import openvpn_server
    from Networking.MiniNet.mininet import mininet_network
    from Networking.OpenVPN.network import get_local_ip
    from Service.ConnectionHandler import start_join_server

    # Validate the requested preset exists before doing any network work.
    if preset_name not in PRESET_CONFIGS:
        print(f"Unknown preset '{preset_name}'. Available: {', '.join(PRESET_CONFIGS)}")
        sys.exit(1)

    # Replace the live session rows with the rows defined in the chosen preset.
    session_rows.clear()
    for row in PRESET_CONFIGS[preset_name]:
        session_rows.append({
            'count': row['count'],
            'vendor_name': row['vendor_name'],
            # Resolve the device class by name from the vendor's subclass list, since the preset
            # stores the class reference from a different import path than the vendor dictionary uses.
            'device_class': next(
                cls for cls in vendor_dictionary[row['vendor_name']].__subclasses__()
                if cls.__name__ == row['device_class'].__name__.split('.')[-1]
            )
        })

    # Convert the session rows into a flat list of host objects ready for Mininet.
    host_list = build_host_list()
    print(f"[VirtuNet] Quickstart: {preset_name} - {len(host_list)} device(s)")

    # Bring up the OpenVPN server so clients can reach the virtual network.
    print("[VirtuNet] Initializing OpenVPN...")
    openvpn_server.initialize()

    # Build and start the Mininet topology with the resolved host list.
    print("[VirtuNet] Configuring Mininet...")
    mininet_network.configuration(host_list)

    # Start the join server so VPN clients can register themselves as they connect.
    start_join_server()
    # Resolve and print the local IP that clients should use to reach this machine.
    get_local_ip()

    # Print a summary of every virtual device and its assigned Mininet IP.
    print("=" * 40)
    print("Devices:")
    for host, device in mininet_network.get_hosts().items():
        print(f"{device.name}: {host.IP()}")
    print("=" * 40)

    # Block until the user sends SIGINT or SIGTERM; signal handlers will call run_cleanup.
    print("[VirtuNet] Network up. Ctrl+C to stop.")
    try:
        signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure cleanup runs even if something raises inside the try block.
        run_cleanup()

if __name__ == '__main__':
    # Use add_help=False so unrecognised arguments are silently collected rather than causing an error.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--preset', metavar='NAME')
    parser.add_argument('--list-presets', action='store_true')
    # parse_known_args lets NiceGUI's own argv pass through without conflicting with our flags.
    args, _ = parser.parse_known_args()

    if args.list_presets:
        # Print available presets and exit without starting the network or GUI.
        from Logic.Presets import PRESET_CONFIGS
        print("Available presets:", ', '.join(PRESET_CONFIGS))
        sys.exit(0)
    
    # Abort early if not running as root; Mininet and iptables both require it.
    setup.ensure_root()
    # Verify all required system tools (openvpn, mn, avahi-daemon, etc.) are installed.
    setup.check_dependencies()

    # Deferred import: run_cleanup uses Mininet and OpenVPN internals that must not load before dependency checks.
    from Networking.cleanup import run_cleanup
    from Networking.MiniNet.mdns import setup_avahi

    # Configure Avahi so virtual hosts can be resolved by hostname on the local network.
    setup_avahi()
    
    # Register signal handlers so both graceful termination (SIGTERM) and Ctrl+C (SIGINT) trigger cleanup.
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    if args.preset:
        # Run in headless CLI mode; skip all GUI imports and start the network directly.
        cli_quickstart(args.preset)
        sys.exit(0)

    # Import NiceGUI and all page modules now that we know we need the GUI.
    from nicegui import ui, app
    import GUI.Frontpage
    import GUI.SessionSetting
    import GUI.CustomSetup
    import GUI.Lobby
    import GUI.ControlCenter
    import GUI.AfterActionReport

    # Force NiceGUI to use the Qt WebEngine backend for the native window.
    os.environ['PYWEBVIEW_GUI'] = 'qt'
    # Disable the Chrome sandbox, which does not work inside the Mininet network namespace.
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--no-sandbox'
    # Register the async shutdown handler so NiceGUI calls cleanup when the window is closed.
    app.on_shutdown(on_shutdown)
    # Set a minimum window size to prevent the layout from breaking on small displays.
    app.native.window_args['min_size'] = (550, 1000)
    # Set the taskbar and window icon for the native window.
    app.native.start_args['icon'] = 'GUI/Assets/VirtuNetIcon.png'
    # Launch the NiceGUI native window; blocks until the window is closed.
    ui.run(native=True, reload=False, window_size=(1000, 1000), title='VirtuNet', storage_secret='my-super-secret-key-123')
    # Final cleanup after the window closes, in case on_shutdown was not called.
    run_cleanup()