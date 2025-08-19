import socket
import pickle
import struct
import time
import platform
import subprocess
import ipaddress
import select

# Discovery / protocol constants (must match server.py)
DISCOVERY_PORT = 50000
DISCOVERY_MESSAGE = b"DISCOVER_RACE_SERVER"
RESPONSE_PREFIX = b"RACE_SERVER:"   # server replies with: b"RACE_SERVER:192.168.0.107:5555"
DISCOVERY_TIMEOUT = 1.0              # seconds to wait for discovery reply

# === low-level send/recv helpers (TCP) ===
def recvall(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def send_msg(sock, obj):
    data = pickle.dumps(obj)
    header = struct.pack('>I', len(data))
    sock.sendall(header + data)

def recv_msg(sock):
    hdr = recvall(sock, 4)
    if not hdr:
        return None
    size = struct.unpack('>I', hdr)[0]
    data = recvall(sock, size)
    if not data:
        return None
    return pickle.loads(data)

# === network utility functions ===
def get_local_ip(fallback="127.0.0.1"):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # pick the outgoing interface by "connecting" to a public IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            if ip.startswith("127.") or ip == "0.0.0.0":
                ip = fallback
        except Exception:
            ip = fallback
    finally:
        try:
            s.close()
        except Exception:
            pass
    return ip

def get_default_gateway_ip():
    try:
        if platform.system().lower() == "windows":
            result = subprocess.check_output("ipconfig", shell=True, stderr=subprocess.DEVNULL).decode(errors='ignore')
            for line in result.splitlines():
                if "Default Gateway" in line and ":" in line:
                    ip = line.split(":")[-1].strip()
                    try:
                        ipaddress.ip_address(ip)
                        return ip
                    except Exception:
                        continue
        else:
            result = subprocess.check_output("ip route show default", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if result:
                parts = result.split()
                if len(parts) >= 3:
                    return parts[2]
    except Exception:
        pass
    return None

# === discovery: broadcast and listen for server replies / broadcasts ===
def discover_server(timeout=DISCOVERY_TIMEOUT):
    local_ip = get_local_ip()
    # compute subnet broadcast (e.g. 192.168.0.255)
    local_bcast = None
    try:
        parts = local_ip.split('.')
        if len(parts) == 4:
            parts[3] = '255'
            local_bcast = '.'.join(parts)
    except Exception:
        local_bcast = None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except Exception:
        pass

    # bind to DISCOVERY_PORT so we receive periodic broadcaster packets sent to that port
    try:
        sock.bind(('', DISCOVERY_PORT))
    except Exception:
        # if binding DISCOVERY_PORT fails, fall back to ephemeral port
        try:
            sock.bind(('', 0))
        except Exception:
            return None

    # destinations: subnet broadcast, generic broadcast, and gateway as direct fallback
    destinations = []
    if local_bcast:
        destinations.append(local_bcast)
    destinations.append('<broadcast>')
    destinations.append('255.255.255.255')

    gateway = get_default_gateway_ip()
    if gateway:
        destinations.append(gateway)

    # send discovery ping to destinations
    for dest in destinations:
        try:
            sock.sendto(DISCOVERY_MESSAGE, (dest, DISCOVERY_PORT))
        except Exception:
            pass

    end_time = time.time() + timeout
    while time.time() < end_time:
        remaining = end_time - time.time()
        if remaining <= 0:
            break
        try:
            ready, _, _ = select.select([sock], [], [], remaining)
        except Exception:
            break
        if not ready:
            break
        try:
            data, addr = sock.recvfrom(2048)
        except Exception:
            continue
        if not data:
            continue

        if data.startswith(RESPONSE_PREFIX):
            payload = data[len(RESPONSE_PREFIX):].decode(errors='ignore').strip()
            if ':' in payload:
                ip_str, port_str = payload.split(':', 1)
                try:
                    ipaddress.ip_address(ip_str)
                    port_int = int(port_str)
                    sock.close()
                    return (ip_str, port_int)
                except Exception:
                    continue
        else:
            txt = data.decode(errors='ignore').strip()
            if ':' in txt:
                potential_ip = txt.split(':', 1)[0]
                try:
                    ipaddress.ip_address(potential_ip)
                    port_int = int(txt.split(':', 1)[1]) if ':' in txt else 5555
                    sock.close()
                    return (potential_ip, port_int)
                except Exception:
                    continue
            try:
                ipaddress.ip_address(txt)
                sock.close()
                return (txt, 5555)
            except Exception:
                continue

    try:
        sock.close()
    except Exception:
        pass
    return None


# === Network client wrapper used by your game ===
class Network:
    def __init__(self, server_host=None, port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # small connect timeout so program doesn't hang too long
        self.client.settimeout(4.0)
        self.port = port

        # If server_host explicitly given, use it. Otherwise try LAN discovery.
        server_addr = None
        if server_host:
            server_addr = (server_host, port)
        else:
            found = discover_server(timeout=DISCOVERY_TIMEOUT)
            if found:
                server_addr = (found[0], found[1])
                print(f"[network] Discovered server at {server_addr[0]}:{server_addr[1]}")
            else:
                # Try direct local candidates (useful when server and client are on same machine)
                tried = []
                candidates = []
                # local interface IP (e.g. 192.168.x.y)
                try:
                    candidates.append(get_local_ip())
                except Exception:
                    pass
                # loopback
                candidates.append('127.0.0.1')
                # hostname (might resolve to local IP)
                try:
                    candidates.append(socket.gethostname())
                except Exception:
                    pass

                # try to connect to candidates (short, non-blocking attempts)
                for cand in candidates:
                    if not cand:
                        continue
                    if cand in tried:
                        continue
                    tried.append(cand)
                    try:
                        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        test_sock.settimeout(0.5)  # very short probe
                        test_sock.connect((cand, port))
                        test_sock.close()
                        server_addr = (cand, port)
                        print(f"[network] Connected directly to local candidate {cand}:{port}")
                        break
                    except Exception:
                        try:
                            test_sock.close()
                        except Exception:
                            pass
                        continue

                # If no local candidate worked, fall back to gateway as before
                if not server_addr:
                    gateway = get_default_gateway_ip()
                    if gateway:
                        print("Discovery failed; attempting default gateway IP as fallback:", gateway)
                        server_addr = (gateway, port)

        # final fallback: ask user (keeps previous behaviour)
        if not server_addr:
            suggestion = get_local_ip()
            manual = input(f'[ERROR] Enter the server IP (e.g. {suggestion}): ').strip()
            server_addr = (manual, port)

        self.server = server_addr[0]
        self.addr = server_addr

        # Finally attempt the real connection using the existing client socket
        try:
            print(f"Connecting to server at {self.server}:{self.port} ...")
            self.client.connect(self.addr)
        except Exception as e:
            print("Connection failed:", e)
            raise

        init = recv_msg(self.client)
        if not init:
            print("No initial assignment received from server.")
            self.assigned = None
        else:
            self.assigned = init

    def get_initial_assignment(self):
        return self.assigned

    def send(self, player):
        try:
            send_msg(self.client, player.get_state())
        except Exception as e:
            print("Network send error:", e)
            return None

        try:
            players_list = recv_msg(self.client)
            return players_list
        except Exception:
            return None
