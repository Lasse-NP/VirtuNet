import random
import socket
import string
import subprocess
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

from Networking.MiniNet.mininet import mininet_network
from Networking.OpenVPN.network import get_local_ip
from Networking.OpenVPN.pki import gen_client
from Networking.config import runtime_config


class ReusableHTTPServer(HTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

_server: ReusableHTTPServer | None = None
_thread: threading.Thread | None = None
_active_code: str | None = None
_port_diagnostics: str | None = None

#Creates a random string with 6 characters
def _make_code(length=6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

class _Handler(BaseHTTPRequestHandler):
    #Defines simple get router, every get request will hit this function
    def do_GET(self):

        #Splits the routing to extract the code from the routing
        parts = self.path.strip("/").split("/")

        #If the split does not have 2 something is wrong
        if len(parts) != 2:
            self._respond(400, "Expected /Code/Name")
            return

        #Creates variable for code and name from the routing
        code, name = parts[0].upper(), parts[1]

        #If the join code does not match the code generated throw code 403 Forbidden
        if code != _active_code:
            self._respond(403, "Invalid Join Code")
            return

        #This creates another routing, writing to the host files
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
        #Checks if name is (a-z, A-Z) or a digit (0-9)
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

    #Creates the respond with the code and message
    def _respond(self, code, msg):
        body = msg.encode()
        self.send_response(code)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

def _generate_port_diagnostics(port: int) -> str:
    lines = [f"Port {port} conflict diagnostics:"]
    try:
        result = subprocess.run(["netstat", "-tlnp"], capture_output=True, text=True)
        matched = [
            line for line in result.stdout.splitlines()
            if f":{port}" in line or "Proto" in line or "Active" in line
        ]
        lines += matched if matched else [f"No netstat entries found for port {port}."]
    except Exception as e:
        lines.append(f"netstat failed: {e}")
    return "\n".join(lines)

def get_port_diagnostics() -> str | None:
    return _port_diagnostics

def start_join_server() -> str | None:
    global _server, _thread, _active_code, _port_diagnostics

    #If server is up, shut it down
    if _server:
        stop_join_server()

    #Finds the port to start the server
    port = runtime_config['join_server_port']

    try:
        #Creates a join code and sets the variable
        _active_code = _make_code()

        #Starts the http server
        _server = ReusableHTTPServer(("0.0.0.0", port), _Handler)
    except OSError as e:
        print(f"[VirtuNet] ERROR: Could not bind join server to port {port}: {e}")
        _port_diagnostics = _generate_port_diagnostics(port)
        print(_port_diagnostics)
        _server = None
        _active_code = None
        return None
    except Exception as e:
        print(f"[VirtuNet] ERROR: Unexpected error starting join server: {e}")
        _server = None
        _active_code = None
        return None

    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()

    try:
        ip = get_local_ip()
    except Exception:
        ip = "unknown"

    print(f"[VirtuNet] Join server running on {ip}:{port}")
    print(f"[VirtuNet] Join code: {_active_code}")
    return _active_code

#Function for starting the http server
def stop_join_server():
    global _server, _thread, _active_code
    if _server:
        _server.shutdown()
        _server.server_close()
        _server = None
    _active_code = None