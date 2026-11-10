"""
MeetLAN - Panel Flotante de Control de Videollamada en Curso
Comunicaciones Multimedia - Universidad de Cuenca
"""

import tkinter as tk
import time

class CallControlBar(tk.Toplevel):
    def __init__(self, parent, peer_info, on_hangup):
        super().__init__(parent)
        self.peer_info = peer_info
        self.on_hangup = on_hangup
        
        self.title("MeetLAN - Control de Llamada")
        
        # Posicionamiento dinámico adaptativo a la resolución de pantalla
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        bar_w = 460
        bar_h = 120
        x = max(10, (screen_w - bar_w) // 2)
        y = max(30, screen_h - bar_h - 70)
        self.geometry(f"{bar_w}x{bar_h}+{x}+{y}")
        self.resizable(False, False)
        self.configure(bg="#11111b")
        self.attributes("-topmost", True)
        
        self.start_time = time.time()
        self.is_running = True

        # Contenedor principal
        f = tk.Frame(self, bg="#11111b")
        f.pack(fill="both", expand=True, padx=15, pady=10)

        # Información del contacto y tiempo
        self.lbl_info = tk.Label(
            f,
            text=f"🟢 En llamada con: {peer_info.get('name', 'Compañero')} ({peer_info.get('ip', '')})",
            bg="#11111b",
            fg="#a6e3a1",
            font=("Segoe UI", 11, "bold")
        )
        self.lbl_info.pack(pady=2)

        self.lbl_timer = tk.Label(
            f,
            text="Duración: 00:00",
            bg="#11111b",
            fg="#cdd6f4",
            font=("Segoe UI", 10)
        )
        self.lbl_timer.pack(pady=2)

        # Botón de Colgar
        self.btn_hangup = tk.Button(
            f,
            text="  🔴 Colgar Videollamada  ",
            bg="#f38ba8",
            fg="#11111b",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            activebackground="#eba0ac",
            command=self._hangup_clicked
        )
        self.btn_hangup.pack(pady=4)

        # Capturar el cierre de ventana [X] para que siempre cuelgue y libere recursos
        self.protocol("WM_DELETE_WINDOW", self._hangup_clicked)

        # Loop de actualización del cronómetro
        self._update_timer()

    def _update_timer(self):
        if not self.is_running:
            return
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        try:
            self.lbl_timer.config(text=f"Duración: {mins:02d}:{secs:02d}")
            self.after(1000, self._update_timer)
        except Exception:
            pass

    def _hangup_clicked(self):
        if not self.is_running:
            return
        self.is_running = False
        try:
            self.btn_hangup.config(state="disabled", text=" Colgando... ")
        except Exception:
            pass
        if self.on_hangup:
            self.on_hangup()
        try:
            self.destroy()
        except Exception:
            pass

    def close_bar(self):
        self.is_running = False
        try:
            self.destroy()
        except Exception:
            pass
