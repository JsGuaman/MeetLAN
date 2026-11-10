"""
MeetLAN - Ventana Principal y Dashboard de Descubrimiento P2P
Comunicaciones Multimedia - Universidad de Cuenca
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

from config import load_config, save_config, get_local_ip
from signaling import SignalingManager
from audio_alert import RingtoneManager
from engine import MediaEngine
from ui_config import ConfigDialog
from ui_call import CallControlBar

class MeetLANApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MeetLAN - Sistema de Videollamada P2P en Tiempo Real")
        
        # Geometría adaptativa y centrada en pantalla
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w = min(700, max(600, screen_w - 60))
        h = min(600, max(480, screen_h - 80))
        x = max(10, (screen_w - w) // 2)
        y = max(10, (screen_h - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(600, 460)
        self.root.configure(bg="#181825")

        self.config = load_config()
        self.local_ip = get_local_ip()
        
        # Gestores de lógica
        self.ringtone = RingtoneManager()
        self.engine = MediaEngine(self.config)
        self.signaling = SignalingManager(
            config=self.config,
            on_peer_discovered=self._on_peers_updated,
            on_incoming_call=self._on_incoming_call_received,
            on_call_accepted=self._on_call_accepted_received,
            on_call_rejected=self._on_call_rejected_received,
            on_call_hungup=self._on_call_hungup_received,
            on_call_busy=self._on_call_busy_received
        )

        self.active_peer = None
        self.call_control_bar = None
        self.outgoing_dialog = None
        self.incoming_dialog = None

        self._build_ui()

        # Iniciar señalización en hilo
        self.root.after(100, self._start_network)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_network(self):
        self.signaling.start(self.local_ip)
        self._update_status_bar()

    def _build_ui(self):
        # 1. Encabezado Superior (Perfil y Estado)
        header_frame = tk.Frame(self.root, bg="#1e1e2e", height=85)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        # Logo / Título
        title_box = tk.Frame(header_frame, bg="#1e1e2e")
        title_box.pack(side="left", padx=15, pady=12)

        lbl_logo = tk.Label(title_box, text="📹 MeetLAN", font=("Segoe UI", 16, "bold"), bg="#1e1e2e", fg="#89b4fa")
        lbl_logo.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text="Comunicaciones Multimedia • ITU-T H.264 & AAC", font=("Segoe UI", 8), bg="#1e1e2e", fg="#a6adc8")
        lbl_sub.pack(anchor="w")

        # Info de Usuario Local
        user_box = tk.Frame(header_frame, bg="#1e1e2e")
        user_box.pack(side="right", padx=15, pady=12)

        self.lbl_user_name = tk.Label(user_box, text=f"👤 {self.config.get('user_name', 'Usuario')}", font=("Segoe UI", 11, "bold"), bg="#1e1e2e", fg="#cdd6f4")
        self.lbl_user_name.pack(anchor="e")

        self.lbl_ip = tk.Label(user_box, text=f"IP Wi-Fi: {self.local_ip}", font=("Consolas", 9), bg="#1e1e2e", fg="#a6e3a1")
        self.lbl_ip.pack(anchor="e")

        self.lbl_dev_info = tk.Label(user_box, text=self._format_dev_info(), font=("Segoe UI", 8), bg="#1e1e2e", fg="#89dceb")
        self.lbl_dev_info.pack(anchor="e")

        # 2. Barra de Herramientas (Escanear, Configuración, Llamada Directa)
        tool_frame = tk.Frame(self.root, bg="#181825")
        tool_frame.pack(fill="x", padx=15, pady=5)

        btn_scan = tk.Button(
            tool_frame, text=" 🔄 Escanear Red LAN ", bg="#89b4fa", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5, command=self._scan_clicked
        )
        btn_scan.pack(side="left", padx=(0, 10))

        btn_config = tk.Button(
            tool_frame, text=" ⚙️ Configuración ", bg="#45475a", fg="#cdd6f4",
            font=("Segoe UI", 9), relief="flat", padx=10, pady=5, command=self._open_config
        )
        btn_config.pack(side="left", padx=(0, 10))

        btn_firewall = tk.Button(
            tool_frame, text=" 🛡️ Firewall ", bg="#fab387", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5, command=self._open_firewall_clicked
        )
        btn_firewall.pack(side="left")

        # Entrada para marcar IP directa
        direct_frame = tk.Frame(tool_frame, bg="#181825")
        direct_frame.pack(side="right")

        tk.Label(direct_frame, text="IP Manual:", bg="#181825", fg="#a6adc8", font=("Segoe UI", 9)).pack(side="left", padx=4)
        self.entry_manual_ip = tk.Entry(direct_frame, bg="#313244", fg="#cdd6f4", width=14, font=("Consolas", 10), insertbackground="white")
        self.entry_manual_ip.pack(side="left", padx=2)
        self.entry_manual_ip.insert(0, "192.168.18.105")

        tk.Label(direct_frame, text="Puerto TX:", bg="#181825", fg="#a6adc8", font=("Segoe UI", 9)).pack(side="left", padx=(6, 2))
        self.entry_manual_tx_port = tk.Entry(direct_frame, bg="#313244", fg="#cdd6f4", width=6, font=("Consolas", 10), insertbackground="white")
        self.entry_manual_tx_port.pack(side="left", padx=2)
        self.entry_manual_tx_port.insert(0, str(self.config.get("tx_port", 5000)))

        btn_call_manual = tk.Button(
            direct_frame, text=" 📞 Llamar ", bg="#a6e3a1", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=8, pady=3, command=self._call_manual_clicked
        )
        btn_call_manual.pack(side="left", padx=4)

        # 3. Lista de Dispositivos Conectados en LAN
        list_container = tk.Frame(self.root, bg="#181825")
        list_container.pack(fill="both", expand=True, padx=15, pady=10)

        lbl_section = tk.Label(list_container, text="Dispositivos detectados con MeetLAN en tu red:", font=("Segoe UI", 10, "bold"), bg="#181825", fg="#cdd6f4")
        lbl_section.pack(anchor="w", pady=(0, 6))

        # Canvas con scroll para los contactos
        self.canvas_peers = tk.Canvas(list_container, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas_peers.yview)
        self.scroll_frame = tk.Frame(self.canvas_peers, bg="#1e1e2e")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas_peers.configure(scrollregion=self.canvas_peers.bbox("all"))
        )

        self.canvas_peers.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=620)
        self.canvas_peers.configure(yscrollcommand=scrollbar.set)

        self.canvas_peers.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 4. Barra de Estado Inferior
        self.status_bar = tk.Label(
            self.root, text="🟢 Sistema listo • Estado: Disponible",
            bg="#11111b", fg="#a6e3a1", font=("Segoe UI", 9), anchor="w", padx=15, pady=4
        )
        self.status_bar.pack(fill="x", side="bottom")

        # Mensaje placeholder en la lista
        self.lbl_no_peers = tk.Label(
            self.scroll_frame,
            text="\n\n🔍 Buscando computadoras en la red con MeetLAN...\nPresiona 'Escanear Red LAN' si tu compañero acaba de abrir la app.",
            bg="#1e1e2e", fg="#6c7086", font=("Segoe UI", 10)
        )
        self.lbl_no_peers.pack(pady=30)

    def _scan_clicked(self):
        self.status_bar.config(text="🔄 Buscando dispositivos en la red LAN...", fg="#89b4fa")
        self.signaling.scan_peers()
        
        # Sondeo directo a la IP manual indicada por si el router Wi-Fi aísla broadcasts
        manual_ip = self.entry_manual_ip.get().strip()
        if manual_ip and manual_ip != self.local_ip:
            import json
            direct_msg = json.dumps({
                "type": "DISCOVERY_PING",
                "name": self.config.get("user_name", "Usuario"),
                "ip": self.local_ip,
                "port": self.signaling.port,
                "status": self.signaling.status
            }).encode("utf-8")
            for p in [self.signaling.port, 6000, 6007, 6010, 6020, 6050]:
                try:
                    self.signaling.sock.sendto(direct_msg, (manual_ip, p))
                except Exception:
                    pass
                    
        self.root.after(1500, self._update_status_bar)

    def _open_config(self):
        ConfigDialog(self.root, self.config, on_saved=self._on_config_saved)

    def _open_firewall_clicked(self):
        """Abre los puertos de MeetLAN en el firewall del sistema con 1 solo clic."""
        from firewall_helper import apply_firewall_rules
        sig_p = self.config.get("signaling_port", 6010)
        rx_p = self.config.get("rx_port", 5200)
        
        ok, msg = apply_firewall_rules([sig_p, rx_p], self.config)
        if ok:
            messagebox.showinfo("Firewall del Sistema", f"🛡️ Configuración de Firewall:\n\n{msg}")
        else:
            messagebox.showwarning("Firewall del Sistema", f"⚠️ Aviso de Firewall:\n\n{msg}")

    def _format_dev_info(self):
        is_win = self.config.get("os_type") == "Windows"
        if is_win:
            v = self.config.get("devices", {}).get("windows", {}).get("video", "Cámara")
            a = self.config.get("devices", {}).get("windows", {}).get("audio_friendly", "Micrófono")
        else:
            v = self.config.get("devices", {}).get("linux", {}).get("video", "/dev/video0")
            a = self.config.get("devices", {}).get("linux", {}).get("audio", "default")
        
        # Recortar nombres largos para que no desborden
        if len(v) > 22: v = v[:20] + ".."
        if len(a) > 22: a = a[:20] + ".."
        return f"📹 {v}  |  🎙️ {a}"

    def _on_config_saved(self, new_cfg):
        self.config = new_cfg
        self.lbl_user_name.config(text=f"👤 {self.config.get('user_name', 'Usuario')}")
        self.lbl_dev_info.config(text=self._format_dev_info())
        self.engine.config = new_cfg
        self.signaling.config = new_cfg
        self.signaling.user_name = new_cfg.get("user_name", "Usuario")
        if hasattr(self, "entry_manual_tx_port"):
            self.entry_manual_tx_port.delete(0, tk.END)
            self.entry_manual_tx_port.insert(0, str(new_cfg.get("tx_port", 5000)))

    def _update_status_bar(self):
        st = self.signaling.status
        if st == "AVAILABLE":
            self.status_bar.config(text=f"🟢 Sistema listo • Estado: Disponible (Puerto {self.signaling.port})", fg="#a6e3a1")
        else:
            self.status_bar.config(text=f"🔴 En llamada con {self.active_peer.get('name', '')} ({self.active_peer.get('ip', '')})", fg="#f38ba8")

    def _on_peers_updated(self, peers):
        self.root.after(0, self._render_peer_list, peers)

    def _render_peer_list(self, peers):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not peers:
            lbl = tk.Label(
                self.scroll_frame,
                text="\n\nNo se han detectado otros dispositivos en la red aún.\nAsegúrate de que tu compañero tenga abierta la aplicación MeetLAN.",
                bg="#1e1e2e", fg="#6c7086", font=("Segoe UI", 10)
            )
            lbl.pack(pady=30)
            return

        for ip, p in peers.items():
            card = tk.Frame(self.scroll_frame, bg="#313244", relief="flat")
            card.pack(fill="x", padx=10, pady=5)

            # Icono y nombre
            info_sub = tk.Frame(card, bg="#313244")
            info_sub.pack(side="left", padx=12, pady=10)

            name_lbl = tk.Label(info_sub, text=f"💻 {p.get('name', 'Compañero')}", font=("Segoe UI", 11, "bold"), bg="#313244", fg="#cdd6f4")
            name_lbl.pack(anchor="w")

            status_txt = "🟢 Disponible" if p.get("status") == "AVAILABLE" else "🔴 En llamada"
            ip_lbl = tk.Label(info_sub, text=f"IP: {ip}  •  {status_txt}", font=("Consolas", 9), bg="#313244", fg="#a6adc8")
            ip_lbl.pack(anchor="w")

            # Botón de Llamar
            btn_state = "normal" if p.get("status") == "AVAILABLE" else "disabled"
            btn_call = tk.Button(
                card, text=" 📞 Llamar ", bg="#a6e3a1", fg="#11111b",
                font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=5,
                state=btn_state,
                command=lambda target_ip=ip, peer_data=p: self._start_call_to(target_ip, peer_data)
            )
            btn_call.pack(side="right", padx=12, pady=10)

    def _call_manual_clicked(self):
        target_ip = self.entry_manual_ip.get().strip()
        if not target_ip:
            messagebox.showwarning("Atención", "Por favor ingresa una IP de destino.")
            return

        try:
            target_tx_port = int(self.entry_manual_tx_port.get().strip())
        except Exception:
            target_tx_port = int(self.config.get("tx_port", 5000))

        self._start_call_to(target_ip, {
            "name": f"PC ({target_ip})",
            "ip": target_ip,
            "remote_rx_port": target_tx_port
        })

    def _start_call_to(self, target_ip, peer_data):
        if self.signaling.status == "IN_CALL":
            messagebox.showwarning("Llamada", "Ya te encuentras en una llamada activa.")
            return

        self.active_peer = peer_data
        self.signaling.send_call_offer(target_ip)
        self._show_outgoing_call_dialog(peer_data)

    def _center_toplevel(self, win, w, h):
        self.root.update_idletasks()
        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        x = max(10, rx + (rw - w) // 2)
        y = max(10, ry + (rh - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _show_outgoing_call_dialog(self, peer_data):
        self.outgoing_dialog = tk.Toplevel(self.root)
        self.outgoing_dialog.title("Llamando...")
        self._center_toplevel(self.outgoing_dialog, 360, 180)
        self.outgoing_dialog.resizable(False, False)
        self.outgoing_dialog.configure(bg="#1e1e2e")
        self.outgoing_dialog.transient(self.root)
        self.outgoing_dialog.grab_set()

        lbl_calling = tk.Label(
            self.outgoing_dialog,
            text=f"📞 Llamando a {peer_data.get('name', 'Compañero')}...",
            font=("Segoe UI", 12, "bold"), bg="#1e1e2e", fg="#89b4fa"
        )
        lbl_calling.pack(pady=(25, 10))

        lbl_wait = tk.Label(
            self.outgoing_dialog,
            text=f"Destino: {peer_data.get('ip')}\nEsperando a que acepte la llamada...",
            font=("Segoe UI", 9), bg="#1e1e2e", fg="#cdd6f4"
        )
        lbl_wait.pack(pady=5)

        btn_cancel = tk.Button(
            self.outgoing_dialog, text="Cancelar", bg="#f38ba8", fg="#11111b",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=4,
            command=self._cancel_outgoing_call
        )
        btn_cancel.pack(pady=15)

    def _cancel_outgoing_call(self):
        if self.active_peer:
            self.signaling.send_hangup(self.active_peer.get("ip"))
        if self.outgoing_dialog:
            self.outgoing_dialog.destroy()
            self.outgoing_dialog = None
        self.active_peer = None

    def _on_incoming_call_received(self, payload):
        self.root.after(0, self._show_incoming_call_dialog, payload)

    def _show_incoming_call_dialog(self, payload):
        caller_name = payload.get("caller_name", "Compañero")
        caller_ip = payload.get("caller_ip", "")
        caller_rx_port = int(payload.get("caller_rx_port", 5200))
        self.active_peer = {
            "name": caller_name,
            "ip": caller_ip,
            "remote_rx_port": caller_rx_port,
            "payload": payload
        }

        # 1. Iniciar timbre audible repetido
        self.ringtone.start_ringing()

        # 2. Mostrar diálogo modal con Aceptar y Rechazar
        self.incoming_dialog = tk.Toplevel(self.root)
        self.incoming_dialog.title("Llamada Entrante")
        self._center_toplevel(self.incoming_dialog, 380, 210)
        self.incoming_dialog.resizable(False, False)
        self.incoming_dialog.configure(bg="#1e1e2e")
        self.incoming_dialog.attributes("-topmost", True)

        lbl_title = tk.Label(
            self.incoming_dialog, text="🔔 ¡LLAMADA ENTRANTE!",
            font=("Segoe UI", 14, "bold"), bg="#1e1e2e", fg="#f9e2af"
        )
        lbl_title.pack(pady=(20, 8))

        lbl_info = tk.Label(
            self.incoming_dialog,
            text=f"Usuario: {caller_name}\nDirección IP: {caller_ip}",
            font=("Segoe UI", 10), bg="#1e1e2e", fg="#cdd6f4"
        )
        lbl_info.pack(pady=5)

        btn_box = tk.Frame(self.incoming_dialog, bg="#1e1e2e")
        btn_box.pack(pady=18)

        btn_accept = tk.Button(
            btn_box, text=" ✔️ Aceptar ", bg="#a6e3a1", fg="#11111b",
            font=("Segoe UI", 11, "bold"), relief="flat", padx=15, pady=6,
            command=self._accept_incoming_call
        )
        btn_accept.pack(side="left", padx=10)

        btn_reject = tk.Button(
            btn_box, text=" ✖️ Rechazar ", bg="#f38ba8", fg="#11111b",
            font=("Segoe UI", 11, "bold"), relief="flat", padx=15, pady=6,
            command=self._reject_incoming_call
        )
        btn_reject.pack(side="left", padx=10)

    def _accept_incoming_call(self):
        # Detener timbre
        self.ringtone.stop_ringing()
        if self.incoming_dialog:
            self.incoming_dialog.destroy()
            self.incoming_dialog = None

        if not self.active_peer:
            return

        target_ip = self.active_peer.get("ip")
        self.signaling.send_call_accept(target_ip)
        
        # Iniciar flujos multimedia
        self._launch_media_session()

    def _reject_incoming_call(self):
        self.ringtone.stop_ringing()
        if self.incoming_dialog:
            self.incoming_dialog.destroy()
            self.incoming_dialog = None

        if self.active_peer:
            self.signaling.send_call_reject(self.active_peer.get("ip"))
        self.active_peer = None

    def _on_call_accepted_received(self, payload):
        self.root.after(0, self._handle_call_accepted, payload)

    def _handle_call_accepted(self, payload):
        if self.outgoing_dialog:
            self.outgoing_dialog.destroy()
            self.outgoing_dialog = None

        callee_rx_port = int(payload.get("callee_rx_port", 5200))
        if self.active_peer:
            self.active_peer["remote_rx_port"] = callee_rx_port

        self._launch_media_session()

    def _launch_media_session(self):
        """Lanza los motores FFmpeg / FFplay con PiP (Fondo remoto + esquina local)."""
        self.signaling.status = "IN_CALL"
        self._update_status_bar()

        remote_ip = self.active_peer.get("ip")
        
        # Negociación P2P Dinámica de Puertos:
        # 1. Escuchar localmente en el puerto RX definido en nuestra configuración
        local_rx = int(self.config.get("rx_port", 5200))
        # 2. Transmitir hacia el puerto RX que el compañero anunció en la señalización
        remote_tx = int(self.active_peer.get("remote_rx_port", self.config.get("tx_port", 5200)))

        print(f"[MEDIA] Negociación de puertos P2P completada exitosamente:")
        print(f"        -> RX Local: Escuchando en 0.0.0.0:{local_rx}")
        print(f"        -> TX Remoto: Transmitiendo hacia {remote_ip}:{remote_tx}")
        self.engine.start_call(remote_ip, remote_tx, local_rx)

        # Mostrar barra flotante de control
        self.call_control_bar = CallControlBar(
            self.root, self.active_peer, on_hangup=self._on_local_hangup
        )

    def _on_local_hangup(self):
        if self.active_peer:
            self.signaling.send_hangup(self.active_peer.get("ip"))
        self.engine.stop_call()
        self.signaling.status = "AVAILABLE"
        self._update_status_bar()
        self.active_peer = None

    def _on_call_rejected_received(self, payload):
        self.root.after(0, self._handle_call_rejected, payload)

    def _handle_call_rejected(self, payload):
        if self.outgoing_dialog:
            self.outgoing_dialog.destroy()
            self.outgoing_dialog = None
        self.active_peer = None
        messagebox.showinfo("Llamada", "El usuario rechazó la llamada.")

    def _on_call_hungup_received(self, payload):
        self.root.after(0, self._handle_call_hungup, payload)

    def _handle_call_hungup(self, payload):
        self.engine.stop_call()
        if self.call_control_bar:
            self.call_control_bar.close_bar()
            self.call_control_bar = None
        self.signaling.status = "AVAILABLE"
        self._update_status_bar()
        self.active_peer = None
        messagebox.showinfo("Llamada", "La videollamada ha finalizado.")

    def _on_call_busy_received(self, payload):
        self.root.after(0, self._handle_call_busy, payload)

    def _handle_call_busy(self, payload):
        if self.outgoing_dialog:
            self.outgoing_dialog.destroy()
            self.outgoing_dialog = None
        self.active_peer = None
        messagebox.showwarning("Llamada", "El usuario se encuentra ocupado en otra llamada.")

    def _on_close(self):
        if self.active_peer:
            self.signaling.send_hangup(self.active_peer.get("ip"))
        self.engine.stop_call()
        self.signaling.stop()
        self.ringtone.stop_ringing()
        self.root.destroy()
