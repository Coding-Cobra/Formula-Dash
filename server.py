# server.py
import socket
import threading
import pickle
import struct
import time
import ipaddress
import platform
import subprocess
import sys

# === CONFIG ===
PORT = 5555
DISCOVERY_PORT = 50000
DISCOVERY_MESSAGE = b"DISCOVER_RACE_SERVER"
RESPONSE_PREFIX = b"RACE_SERVER:"    # response: b"RACE_SERVER:192.168.0.107:5555"
BROADCAST_INTERVAL = 3.0              # seconds for periodic broadcaster

# === helpers ===
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

def get_local_ip(fallback="127.0.0.1"):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
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

# === discovery responder (reply to UDP pings) ===
def discovery_responder(tcp_port, bind_ip=""):
    """
    Listen for DISCOVERY_MESSAGE on DISCOVERY_PORT and reply with
    RESPONSE_PREFIX + "<server_ip>:<tcp_port>".
    bind_ip: '' (all interfaces) or specific local interface IP.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((bind_ip, DISCOVERY_PORT))
    except Exception as e:
        print(f"[discovery] WARNING: cannot bind discovery UDP port {DISCOVERY_PORT} on '{bind_ip}': {e}")
        return

    print(f"[discovery] Listening for discovery on UDP port {DISCOVERY_PORT} (bind={bind_ip})")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if not data:
                continue
            # Accept exact message or anything that starts with DISCOVER
            if data == DISCOVERY_MESSAGE or data.startswith(b"DISCOVER"):
                server_ip = get_local_ip()
                resp = RESPONSE_PREFIX + f"{server_ip}:{tcp_port}".encode()
                # reply back to the source address (client)
                try:
                    sock.sendto(resp, addr)
                except Exception as e:
                    # transient send errors are fine
                    print(f"[discovery] sendto failed to {addr}: {e}")
        except Exception as e:
            print("[discovery] error:", e)
            time.sleep(0.5)

# === optional periodic broadcaster (helps in networks where broadcast replies blocked) ===
def periodic_broadcaster(local_ip, tcp_port, interval=BROADCAST_INTERVAL):
    """
    Periodically broadcast "RACE_SERVER:<ip>:<port>" to broadcast addresses on DISCOVERY_PORT.
    Also attempts the subnet broadcast (e.g. 192.168.0.255) which is often more reliable.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except Exception:
        pass

    msg = RESPONSE_PREFIX + f"{local_ip}:{tcp_port}".encode()
    print(f"[bcast] Periodic broadcaster sending on UDP {DISCOVERY_PORT} every {interval}s")
    # compute subnet broadcast (best-effort)
    try:
        parts = local_ip.split('.')
        if len(parts) == 4:
            parts[3] = '255'
            local_bcast = '.'.join(parts)
        else:
            local_bcast = None
    except Exception:
        local_bcast = None

    while True:
        try:
            # try subnet broadcast first (most specific)
            if local_bcast:
                try:
                    sock.sendto(msg, (local_bcast, DISCOVERY_PORT))
                except Exception:
                    pass
            # then try system broadcast token and global broadcast
            try:
                sock.sendto(msg, ('<broadcast>', DISCOVERY_PORT))
            except Exception:
                try:
                    sock.sendto(msg, ('255.255.255.255', DISCOVERY_PORT))
                except Exception:
                    pass
        except Exception as e:
            print("[bcast] broadcast error:", e)
        time.sleep(interval)

# === Game state (keeps compatibility with existing client-side code) ===
players = [
    {"id": i+1, "name":'bot', "pos": (100 + i*40, 100), "angle": 0, "color": (255,255,255), "velocity": (0,0), "active": False,
     "ready": False, "last checkpoint": 0, "check_distance":100, "prev_check_distance":100,"current_lap": 0, "fastes_lap": 999999,
     "time_to_prev_point": 1000, "time_to_nxt_point": 1000, "ceck_times":[[None,None]], "ceck_times_reset":False, 'race_completed':False,
     "helmet_color":(255,255,255)}
    for i in range(8)
]

available_slots = list(range(len(players)))

def threaded_client(conn, slot_index):
    assigned_id = slot_index + 1
    init = {"assigned_id": assigned_id}
    try:
        send_msg(conn, init)
    except Exception as e:
        print("Failed sending initial assignment:", e)
        conn.close()
        available_slots.append(slot_index)
        return

    players[slot_index]['active'] = True
    players[slot_index]['ready'] = False
    players[slot_index]['id'] = assigned_id
    print(f"Client assigned id={assigned_id}")

    try:
        while True:
            data = recv_msg(conn)
            if data is None:
                print(f"Client {assigned_id} disconnected")
                players[slot_index]['active'] = False
                players[slot_index]['ready'] = True
                break

            data['id'] = assigned_id
            for k in ("name", "pos", "angle", "velocity", "active", "ready", "last checkpoint", "check_distance", "prev_check_distance",
                      "current_lap", "fastes_lap", "color", "helmet_color","time_to_prev_point", "time_to_nxt_point", "ceck_times", 
                      "ceck_times_reset", "race_completed"):
                if k in data:
                    players[slot_index][k] = data[k]

            try:
                send_msg(conn, players)
            except Exception as e:
                print(f"Send to client {assigned_id} failed:", e)
                players[slot_index]['active'] = False
                players[slot_index]['ready'] = True
                break

    except Exception as e:
        print("Threaded client exception:", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        if slot_index not in available_slots:
            available_slots.append(slot_index)
        players[slot_index]['active'] = False
        players[slot_index]['ready'] = True

# === main server loop ===
if __name__ == "__main__":
    local_ip = get_local_ip()
    gateway = get_default_gateway_ip()
    print("Server local IP:", local_ip)
    if gateway:
        print("Detected default gateway (router) IP:", gateway)
    else:
        print("Default gateway IP not detected.")

    # Start discovery responder listening on DISCOVERY_PORT bound to all interfaces.
    # If binding to all interfaces fails on a system, you can change bind_ip to local_ip.
    t = threading.Thread(target=discovery_responder, args=(PORT, ""), daemon=True)
    t.start()

    # Start periodic broadcaster (daemon) to increase discovery reliability
    tb = threading.Thread(target=periodic_broadcaster, args=(local_ip, PORT, BROADCAST_INTERVAL), daemon=True)
    tb.start()

    # Bind TCP listening socket to all interfaces so clients can connect to any host IP
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        listener.bind(('', PORT))
    except Exception as e:
        print("Bind error:", e)
        raise

    listener.listen(20)
    print(f"Server listening on 0.0.0.0:{PORT}  (clients should connect to {local_ip}:{PORT})")

    while True:
        conn, addr = listener.accept()
        print("Connected to:", addr)
        if available_slots:
            slot = available_slots.pop(0)
            threading.Thread(target=threaded_client, args=(conn, slot), daemon=True).start()
        else:
            print("Server full; rejecting client")
            conn.close()
