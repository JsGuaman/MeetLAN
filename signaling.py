"""
MeetLAN - Protocolo de Señalización y Descubrimiento P2P en LAN
Comunicaciones Multimedia - Universidad de Cuenca
"""

import socket
import threading
import json
import time

class SignalingManager:
    def __init__(self, config, on_peer_discovered=None, on_incoming_call=None,
                 on_call_accepted=None, on_call_rejected=None, on_call_hungup=None,
                 on_call_busy=None):
        self.config = config
        self.port = int(config.get("signaling_port", 6000))
        self.local_ip = None
        self.user_name = config.get("user_name", "Usuario")
        self.status = "AVAILABLE"  # "AVAILABLE" | "IN_CALL"
        
        # Callbacks de UI
        self.on_peer_discovered = on_peer_discovered
        self.on_incoming_call = on_incoming_call
        self.on_call_accepted = on_call_accepted
        self.on_call_rejected = on_call_rejected
        self.on_call_hungup = on_call_hungup
        self.on_call_busy = on_call_busy
        
        self.peers = {}  # ip -> {"name": ..., "status": ..., "last_seen": ...}
        self.running = False
        self.sock = None
        self.listener_thread = None
        self._my_ips = set()

    def start(self, local_ip):
        self.local_ip = local_ip
        self.running = True
        self._refresh_my_ips()
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            self.sock.bind(("0.0.0.0", self.port))
            print(f"[SEÑALIZACIÓN] Escuchando en UDP 0.0.0.0:{self.port} (Todas las interfaces de red)")
        except Exception as e:
            print(f"[SEÑALIZACIÓN] Error al enlazar puerto {self.port}: {e}")
            bound = False
            for alt_port in [6010, 6020, 6030, 6050, 7000]:
                try:
                    self.port = alt_port
                    self.sock.bind(("0.0.0.0", self.port))
                    print(f"[SEÑALIZACIÓN] Enlazado exitosamente a puerto alternativo UDP 0.0.0.0:{self.port}")
                    bound = True
                    break
                except Exception:
                    continue
            if not bound:
                print(f"[SEÑALIZACIÓN] Fallo crítico al enlazar socket.")
                return False

        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        
        # Iniciar descubrimiento inicial
        self.scan_peers()
        return True

    def _refresh_my_ips(self):
        try:
            from config import get_available_interfaces
            self._my_ips = set(i["ip"] for i in get_available_interfaces()) | {"127.0.0.1", "0.0.0.0", self.local_ip}
        except Exception:
            self._my_ips = {"127.0.0.1", "0.0.0.0", self.local_ip}

    def update_local_ip(self, new_ip):
        """Actualiza la IP local anunciada cuando el usuario cambia de interfaz en la UI."""
        self.local_ip = new_ip
        self._refresh_my_ips()
        self.scan_peers()

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

    def scan_peers(self):
        """Envía saludo broadcast y sondeo rápido a todas las subredes IPv4 conocidas."""
        if not self.sock or not self.local_ip:
            return
        
        msg = json.dumps({
            "type": "DISCOVERY_PING",
            "name": self.user_name,
            "ip": self.local_ip,
            "port": self.port,
            "status": self.status
        }).encode("utf-8")

        ports_to_broadcast = set([self.port, 6000, 6005, 6007, 6010, 6020, 6050])
        
        # Recolectar broadcasts de todas las interfaces disponibles para no perder ninguna subred
        bcast_addresses = set(["255.255.255.255"])
        subnets_to_probe = []

        try:
            from config import get_available_interfaces
            for iface in get_available_interfaces():
                ip = iface.get("ip", "")
                parts = ip.split(".")
                if len(parts) == 4:
                    bcast_addresses.add(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
                    subnets_to_probe.append(ip)
        except Exception:
            pass

        parts = self.local_ip.split(".")
        if len(parts) == 4:
            bcast_addresses.add(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
            if self.local_ip not in subnets_to_probe:
                subnets_to_probe.insert(0, self.local_ip)

        # 1. Broadcast global y en cada subred específica
        for p in ports_to_broadcast:
            for bcast_ip in bcast_addresses:
                try:
                    self.sock.sendto(msg, (bcast_ip, p))
                except Exception:
                    pass

        # 2. Sondeo en hilo de fondo a las subredes activas
        threading.Thread(target=self._subnet_ping_worker, args=(msg, subnets_to_probe), daemon=True).start()

    def _subnet_ping_worker(self, msg, ip_list=None):
        ports_to_probe = [self.port, 6000, 6007, 6010, 6050]
        if not ip_list:
            ip_list = [self.local_ip]

        scanned_bases = set()
        for ref_ip in ip_list:
            parts = ref_ip.split(".")
            if len(parts) != 4:
                continue
            base = f"{parts[0]}.{parts[1]}.{parts[2]}"
            if base in scanned_bases:
                continue
            scanned_bases.add(base)
            my_last = int(parts[3])
            
            for host in range(1, 255):
                if host == my_last:
                    continue
                target_ip = f"{base}.{host}"
                for p in ports_to_probe:
                    try:
                        self.sock.sendto(msg, (target_ip, p))
                    except Exception:
                        pass
                time.sleep(0.002)

    def send_call_offer(self, target_ip):
        """Inicia una llamada hacia target_ip comunicando el puerto RX configurado."""
        self.status = "CALLING"
        rx_port = int(self.config.get("rx_port", 5200))
        msg = json.dumps({
            "type": "CALL_OFFER",
            "caller_name": self.user_name,
            "caller_ip": self.local_ip,
            "caller_rx_port": rx_port,
            "caller_sig_port": self.port
        }).encode("utf-8")
        
        peer_p = self.peers.get(target_ip, {}).get("port", self.port)
        target_ports = set([peer_p, self.port, 6000, 6007, 6010, 6050])
        for p in target_ports:
            try:
                self.sock.sendto(msg, (target_ip, p))
            except Exception:
                pass
        print(f"[LLAMADA] Oferta de llamada enviada a {target_ip} en puertos {target_ports} (Mi RX espera en UDP {rx_port})")
        return True

    def send_call_accept(self, target_ip):
        """Acepta la llamada entrante comunicando el puerto RX configurado."""
        self.status = "IN_CALL"
        self._current_ringing_caller = None
        rx_port = int(self.config.get("rx_port", 5200))
        msg = json.dumps({
            "type": "CALL_ACCEPT",
            "callee_name": self.user_name,
            "callee_ip": self.local_ip,
            "callee_rx_port": rx_port,
            "callee_sig_port": self.port
        }).encode("utf-8")
        
        peer_p = self.peers.get(target_ip, {}).get("port", self.port)
        target_ports = set([peer_p, self.port, 6000, 6007, 6010, 6050])
        for p in target_ports:
            try:
                self.sock.sendto(msg, (target_ip, p))
            except Exception:
                pass
        print(f"[LLAMADA] Aceptación de llamada enviada a {target_ip} (Mi RX espera en UDP {rx_port})")

    def send_call_reject(self, target_ip):
        """Rechaza la llamada entrante."""
        self.status = "AVAILABLE"
        self._current_ringing_caller = None
        msg = json.dumps({
            "type": "CALL_REJECT",
            "callee_name": self.user_name,
            "reason": "USER_REJECTED"
        }).encode("utf-8")
        peer_p = self.peers.get(target_ip, {}).get("port", self.port)
        target_ports = set([peer_p, self.port, 6000, 6007, 6010, 6050])
        for p in target_ports:
            try:
                self.sock.sendto(msg, (target_ip, p))
            except Exception:
                pass

    def send_hangup(self, target_ip):
        """Finaliza la llamada activa."""
        self.status = "AVAILABLE"
        self._current_ringing_caller = None
        msg = json.dumps({
            "type": "CALL_HANGUP",
            "from_name": self.user_name,
            "from_ip": self.local_ip
        }).encode("utf-8")
        peer_p = self.peers.get(target_ip, {}).get("port", self.port)
        target_ports = set([peer_p, self.port, 6000, 6007, 6010, 6050])
        for p in target_ports:
            try:
                self.sock.sendto(msg, (target_ip, p))
            except Exception:
                pass

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                if not data:
                    continue
                sender_ip = addr[0]
                if sender_ip in self._my_ips:
                    # Ignorar paquetes propios emitidos por cualquier interfaz local
                    continue
                
                # Intentar parsear JSON
                try:
                    payload = json.loads(data.decode("utf-8", errors="ignore"))
                except Exception:
                    # Soporte para el saludo de interciclo antiguo b"LLAMADA"
                    if data.strip() == b"LLAMADA":
                        payload = {"type": "CALL_OFFER", "caller_name": "Terminal", "caller_ip": sender_ip}
                    else:
                        continue
                
                p_type = payload.get("type", "")
                
                # 1. Descubrimiento PING
                if p_type == "DISCOVERY_PING":
                    peer_name = payload.get("name", "Desconocido")
                    peer_status = payload.get("status", "AVAILABLE")
                    peer_port = int(payload.get("port", addr[1]))
                    self.peers[sender_ip] = {
                        "name": peer_name,
                        "ip": sender_ip,
                        "port": peer_port,
                        "status": peer_status,
                        "last_seen": time.time()
                    }
                    if self.on_peer_discovered:
                        self.on_peer_discovered(self.peers)
                    
                    # Responder con PONG comunicando nuestro puerto
                    pong = json.dumps({
                        "type": "DISCOVERY_PONG",
                        "name": self.user_name,
                        "ip": self.local_ip,
                        "port": self.port,
                        "status": self.status
                    }).encode("utf-8")
                    
                    # Enviar respuesta al puerto anunciado por el emisor + puertos estándar
                    reply_ports = set([peer_port, addr[1], 6000, 6007, 6010, 6050])
                    for p in reply_ports:
                        try:
                            self.sock.sendto(pong, (sender_ip, p))
                        except Exception:
                            pass

                # 2. Descubrimiento PONG
                elif p_type == "DISCOVERY_PONG":
                    peer_name = payload.get("name", "Desconocido")
                    peer_status = payload.get("status", "AVAILABLE")
                    peer_port = int(payload.get("port", addr[1]))
                    self.peers[sender_ip] = {
                        "name": peer_name,
                        "ip": sender_ip,
                        "port": peer_port,
                        "status": peer_status,
                        "last_seen": time.time()
                    }
                    if self.on_peer_discovered:
                        self.on_peer_discovered(self.peers)

                # 3. Oferta de llamada entrante
                elif p_type == "CALL_OFFER":
                    if self.status in ["IN_CALL", "RINGING"]:
                        # Si ya está sonando por este mismo llamante, ignorar paquete duplicado
                        if self.status == "RINGING" and getattr(self, "_current_ringing_caller", None) == sender_ip:
                            continue
                        busy_msg = json.dumps({"type": "CALL_BUSY"}).encode("utf-8")
                        peer_p = int(payload.get("caller_sig_port", addr[1]))
                        for p in set([peer_p, addr[1], 6000, 6007, 6010, 6050]):
                            try:
                                self.sock.sendto(busy_msg, (sender_ip, p))
                            except Exception:
                                pass
                    else:
                        self.status = "RINGING"
                        self._current_ringing_caller = sender_ip
                        payload["sender_socket_ip"] = sender_ip
                        if self.on_incoming_call:
                            self.on_incoming_call(payload)

                # 4. Llamada aceptada
                elif p_type == "CALL_ACCEPT":
                    self.status = "IN_CALL"
                    self._current_ringing_caller = None
                    payload["sender_socket_ip"] = sender_ip
                    if self.on_call_accepted:
                        self.on_call_accepted(payload)

                # 5. Llamada rechazada
                elif p_type == "CALL_REJECT":
                    self.status = "AVAILABLE"
                    self._current_ringing_caller = None
                    if self.on_call_rejected:
                        self.on_call_rejected(payload)

                # 6. Colgar llamada
                elif p_type == "CALL_HANGUP":
                    self.status = "AVAILABLE"
                    self._current_ringing_caller = None
                    if self.on_call_hungup:
                        self.on_call_hungup(payload)

                # 7. Usuario ocupado
                elif p_type == "CALL_BUSY":
                    self.status = "AVAILABLE"
                    self._current_ringing_caller = None
                    if self.on_call_busy:
                        self.on_call_busy(payload)

            except Exception as e:
                if self.running:
                    time.sleep(0.05)
