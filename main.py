from nicegui import ui, app
from Networking.cleanup import run_cleanup
import setup
import os

import GUI.Frontpage
import GUI.Lobby
import GUI.SessionSetting
import GUI.ControlCenter
import GUI.AfterActionReport

import asyncio
import sys
import signal

async def on_shutdown():
    await asyncio.to_thread(run_cleanup)

async def handle_signal(sig, frame):
    run_cleanup()
    sys.exit(1)

if __name__ == '__main__':
    os.environ['PYWEBVIEW_GUI'] = 'qt'
    setup.ensure_root()
    setup.check_dependencies()
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    app.on_shutdown(on_shutdown)
    app.native.window_args['min_size'] = (550, 1000)
    ui.run(native=True, reload=False, window_size=(600, 1000), storage_secret='my-super-secret-key-123')
    run_cleanup()