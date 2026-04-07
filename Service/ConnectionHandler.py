import random
import socket
import string
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

from Networking.MiniNet.mininet import mininet_network
from Networking.OpenVPN.network import get_local_ip
from Networking.OpenVPN.pki import gen_client

class ReusableHTTPServer(HTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

PORT = 8080
_server: ReusableHTTPServer | None = None
_thread: threading.Thread | None = None
_active_code: str | None = None

def _make_code(length=6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parts = self.path.strip("/").split("/")

        if len(parts) != 2:
            self._respond(400, "Expected /Code/Name")
            return

        code, name = parts[0].upper(), parts[1]

        if code != _active_code:
            self._respond(403, "Invalid Join Code")
            return

        if name == 'hosts':
            try:
                hosts = mininet_network.get_hosts()
                result = {host.name: host.IP() for host in hosts.keys()}
                body = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._respond(500, f"Failed to get hosts: {e}")
            return

        if not name.isalnum():
            self._respond(400, "Name must be alphanumeric.")
            return

        try:
            ovpn_content = gen_client(name)
        except Exception as e:
            self._respond(500, f"Failed to generate config: {e}")
            return

        self.send_response(200)
        self.send_header("Content-type", "application/x-openvpn-profile")
        self.send_header("Content-Disposition", f'attachment; filename="{name}.ovpn"')
        self.end_headers()
        self.wfile.write(ovpn_content.encode())

    def _respond(self, code, msg):
        body = msg.encode()
        self.send_response(code)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

def start_join_server() -> str:
    global _server, _thread, _active_code

    if _server:
        stop_join_server()

    _active_code = _make_code()
    _server = ReusableHTTPServer(("0.0.0.0", PORT), _Handler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()

    ip = get_local_ip()
    print(f"[VirtuNet] Join server running on {ip}:{PORT}")
    print(f"[VirtuNet] Join code: {_active_code}")
    return _active_code

def stop_join_server():
    global _server, _thread, _active_code
    if _server:
        _server.shutdown()
        _server.server_close()
        _server = None
    _active_code = None