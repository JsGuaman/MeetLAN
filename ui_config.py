"""
MeetLAN - Panel de Configuración de Parámetros de Video/Audio y Red
Comunicaciones Multimedia - Universidad de Cuenca
"""

import tkinter as tk
from tkinter import ttk, messagebox
import platform
from config import save_config
from devices import get_available_devices
from firewall_helper import test_udp_port, apply_firewall_rules

class ConfigDialog(tk.Toplevel):
    def __init__(self, parent, config, on_saved=None):
        super().__init__(parent)
        self.title("Configuración de Parámetros - MeetLAN")
        self.config = config
        self.on_saved = on_saved
        self.is_win = platform.system() == "Windows"
        
        # Tamaño de ventana adaptativo a la resolución de pantalla
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = min(680, max(580, screen_w - 60))
        win_h = min(600, max(460, screen_h - 100))

        # Centrar sobre la ventana padre o la pantalla
        try:
            parent.update_idletasks()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = max(10, px + (pw - win_w) // 2)
            y = max(10, py + (ph - win_h) // 2)
        except Exception:
            x = max(10, (screen_w - win_w) // 2)
            y = max(10, (screen_h - win_h) // 2)

        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.minsize(560, 440)
        self.resizable(True, True)

        self.configure(bg="#1e1e2e")
        self.transient(parent)
        self.grab_set()

        # Cargar dispositivos detectados en hardware
        self.detected_video, self.detected_audio = get_available_devices()

        # Estilo ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4", padding=[12, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#89b4fa")], foreground=[("selected", "#11111b")])
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 9))
        style.configure("TCombobox", fieldbackground="#313244", foreground="#cdd6f4")

        # 1. BOTONES INFERIORES PRIMERO (Garantiza que SIEMPRE sean visibles y accesibles en Linux/Windows)
        btn_frame = tk.Frame(self, bg="#1e1e2e")
        btn_frame.pack(side="bottom", fill="x", padx=15, pady=10)

        btn_cancel = tk.Button(btn_frame, text="Cancelar", bg="#45475a", fg="#cdd6f4", font=("Segoe UI", 10),
                               relief="flat", padx=15, pady=5, command=self.destroy)
        btn_cancel.pack(side="right", padx=5)

        btn_save = tk.Button(btn_frame, text=" Guardar Cambios ", bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 10, "bold"),
                             relief="flat", padx=15, pady=5, command=self._save_changes)
        btn_save.pack(side="right", padx=5)

        # 2. Pestañas (Notebook) ocupando el espacio restante superior
        notebook = ttk.Notebook(self)
        notebook.pack(side="top", fill="both", expand=True, padx=15, pady=(15, 0))

        # Pestañas
        tab_devices = ttk.Frame(notebook)
        tab_video = ttk.Frame(notebook)
        tab_audio = ttk.Frame(notebook)
        tab_network = ttk.Frame(notebook)

        # Dispositivos de Hardware primero (como en Zoom)
        notebook.add(tab_devices, text=" ⚙️ Dispositivos ")
        notebook.add(tab_video, text=" 📹 Video ")
        notebook.add(tab_audio, text=" 🎙️ Audio ")
        notebook.add(tab_network, text=" 🌐 Red / Puertos ")

        # Construir contenido
        self._build_devices_tab(tab_devices)
        self._build_video_tab(tab_video)
        self._build_audio_tab(tab_audio)
        self._build_network_tab(tab_network)

    def _build_devices_tab(self, parent):
        f = tk.Frame(parent, bg="#1e1e2e")
        f.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_desc = tk.Label(
            f,
            text="Selecciona tu cámara y micrófono detectados automáticamente en tu sistema:",
            bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 10, "bold")
        )
        lbl_desc.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 15))

        # 1. Cámara de Video
        tk.Label(f, text="📹 Cámara de Video:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        
        self.video_names = [d["display_name"] for d in self.detected_video]
        self.var_video_choice = tk.StringVar()
        
        # Seleccionar la que coincida con la configuración actual
        curr_v = self._get_current_video_id()
        selected_v = self.video_names[0] if self.video_names else ""
        for d in self.detected_video:
            if d["ffmpeg_id"] == curr_v or d["display_name"] in curr_v:
                selected_v = d["display_name"]
                break
        self.var_video_choice.set(selected_v)

        self.cb_video = ttk.Combobox(f, textvariable=self.var_video_choice, values=self.video_names, state="readonly", width=36)
        self.cb_video.grid(row=1, column=1, sticky="w", padx=5, pady=8)

        # 2. Micrófono de Audio
        tk.Label(f, text="🎙️ Micrófono de Audio:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=8)
        
        self.audio_names = [d["display_name"] for d in self.detected_audio]
        self.var_audio_choice = tk.StringVar()
        
        curr_a = self._get_current_audio_id()
        selected_a = self.audio_names[0] if self.audio_names else ""
        for d in self.detected_audio:
            if d["ffmpeg_id"] == curr_a or d["display_name"] in curr_a or (d.get("alt_id") and d["alt_id"] == curr_a):
                selected_a = d["display_name"]
                break
        self.var_audio_choice.set(selected_a)

        self.cb_audio = ttk.Combobox(f, textvariable=self.var_audio_choice, values=self.audio_names, state="readonly", width=36)
        self.cb_audio.grid(row=2, column=1, sticky="w", padx=5, pady=8)

        # Botón para refrescar dispositivos
        btn_refresh = tk.Button(
            f, text=" 🔄 Actualizar Lista de Dispositivos ", bg="#313244", fg="#cdd6f4",
            font=("Segoe UI", 9), relief="flat", padx=10, pady=4, command=self._refresh_hardware
        )
        btn_refresh.grid(row=3, column=0, columnspan=2, sticky="w", pady=15)

        # Caja de información sobre dispositivos activos
        info_frame = tk.Frame(f, bg="#313244", padx=12, pady=10)
        info_frame.grid(row=4, column=0, columnspan=2, sticky="we", pady=10)
        
        tip_text = (
            "💡 Consejo de Sincronismo (P7 / Interciclo):\n"
            "• Si usas auriculares Bluetooth (ej. ENVTWBUDS), el sistema ajusta el búfer\n"
            "  a 40 ms para eliminar el retardo de 500 ms de Windows.\n"
            "• Si desconectas los auriculares, puedes seleccionar aquí tu micrófono integrado."
        )
        tk.Label(info_frame, text=tip_text, bg="#313244", fg="#a6adc8", font=("Segoe UI", 8), justify="left").pack(anchor="w")

    def _refresh_hardware(self):
        self.detected_video, self.detected_audio = get_available_devices()
        self.video_names = [d["display_name"] for d in self.detected_video]
        self.audio_names = [d["display_name"] for d in self.detected_audio]
        
        self.cb_video["values"] = self.video_names
        self.cb_audio["values"] = self.audio_names
        
        if self.video_names and not self.var_video_choice.get():
            self.var_video_choice.set(self.video_names[0])
        if self.audio_names and not self.var_audio_choice.get():
            self.var_audio_choice.set(self.audio_names[0])
            
        messagebox.showinfo("Hardware", "Lista de cámaras y micrófonos actualizada exitosamente.")

    def _get_current_video_id(self):
        if self.is_win:
            return self.config.get("devices", {}).get("windows", {}).get("video", "")
        return self.config.get("devices", {}).get("linux", {}).get("video", "")

    def _get_current_audio_id(self):
        if self.is_win:
            return self.config.get("devices", {}).get("windows", {}).get("audio", "")
        return self.config.get("devices", {}).get("linux", {}).get("audio", "")

    def _build_video_tab(self, parent):
        f = tk.Frame(parent, bg="#1e1e2e")
        f.pack(fill="both", expand=True, padx=20, pady=20)

        # Bitrate
        tk.Label(f, text="Tasa de Bits de Video (b:v):", bg="#1e1e2e", fg="#cdd6f4").grid(row=0, column=0, sticky="w", pady=6)
        self.var_bitrate = tk.StringVar(value=self.config.get("video_bitrate", "300k"))
        cb_bitrate = ttk.Combobox(f, textvariable=self.var_bitrate, values=["100k", "200k", "300k", "500k", "800k", "1200k"], width=15)
        cb_bitrate.grid(row=0, column=1, sticky="e", pady=6)

        # FPS
        tk.Label(f, text="Tasa de Fotogramas (fps):", bg="#1e1e2e", fg="#cdd6f4").grid(row=1, column=0, sticky="w", pady=6)
        self.var_fps = tk.IntVar(value=self.config.get("fps", 24))
        cb_fps = ttk.Combobox(f, textvariable=self.var_fps, values=[15, 20, 24, 30], width=15)
        cb_fps.grid(row=1, column=1, sticky="e", pady=6)

        # GOP
        tk.Label(f, text="Tamaño de GoP (Cuadros por intra I):", bg="#1e1e2e", fg="#cdd6f4").grid(row=2, column=0, sticky="w", pady=6)
        self.var_gop = tk.IntVar(value=self.config.get("gop", 24))
        cb_gop = ttk.Combobox(f, textvariable=self.var_gop, values=[12, 16, 24, 30, 60], width=15)
        cb_gop.grid(row=2, column=1, sticky="e", pady=6)

        # Preset
        tk.Label(f, text="Preset de Codificación:", bg="#1e1e2e", fg="#cdd6f4").grid(row=3, column=0, sticky="w", pady=6)
        self.var_preset = tk.StringVar(value=self.config.get("preset", "ultrafast"))
        cb_preset = ttk.Combobox(f, textvariable=self.var_preset, values=["ultrafast", "superfast", "veryfast"], width=15)
        cb_preset.grid(row=3, column=1, sticky="e", pady=6)

        # Tune
        tk.Label(f, text="Ajuste de Latencia (Tune):", bg="#1e1e2e", fg="#cdd6f4").grid(row=4, column=0, sticky="w", pady=6)
        self.var_tune = tk.StringVar(value=self.config.get("tune", "zerolatency"))
        cb_tune = ttk.Combobox(f, textvariable=self.var_tune, values=["zerolatency", "none"], width=15)
        cb_tune.grid(row=4, column=1, sticky="e", pady=6)

        # Pixel format
        tk.Label(f, text="Espacio de Color (Aceleración SIMD):", bg="#1e1e2e", fg="#cdd6f4").grid(row=5, column=0, sticky="w", pady=6)
        self.var_pix_fmt = tk.StringVar(value=self.config.get("pix_fmt", "yuv420p"))
        cb_pix = ttk.Combobox(f, textvariable=self.var_pix_fmt, values=["yuv420p", "yuyv422", "nv12"], width=15)
        cb_pix.grid(row=5, column=1, sticky="e", pady=6)

    def _build_audio_tab(self, parent):
        f = tk.Frame(parent, bg="#1e1e2e")
        f.pack(fill="both", expand=True, padx=20, pady=20)

        # Códec
        tk.Label(f, text="Códec de Audio:", bg="#1e1e2e", fg="#cdd6f4").grid(row=0, column=0, sticky="w", pady=6)
        self.var_acodec = tk.StringVar(value=self.config.get("audio_codec", "aac"))
        cb_acodec = ttk.Combobox(f, textvariable=self.var_acodec, values=["aac", "libopus"], width=15)
        cb_acodec.grid(row=0, column=1, sticky="e", pady=6)

        # Bitrate Audio
        tk.Label(f, text="Tasa de Bits de Audio:", bg="#1e1e2e", fg="#cdd6f4").grid(row=1, column=0, sticky="w", pady=6)
        self.var_abitrate = tk.StringVar(value=self.config.get("audio_bitrate", "64k"))
        cb_abitrate = ttk.Combobox(f, textvariable=self.var_abitrate, values=["32k", "48k", "64k", "96k", "128k"], width=15)
        cb_abitrate.grid(row=1, column=1, sticky="e", pady=6)

        # Búfer Audio Bluetooth (DirectShow)
        tk.Label(f, text="Búfer de Audio Hardware (ms):", bg="#1e1e2e", fg="#cdd6f4").grid(row=2, column=0, sticky="w", pady=6)
        self.var_abuf = tk.IntVar(value=self.config.get("audio_buffer_size_ms", 40))
        cb_abuf = ttk.Combobox(f, textvariable=self.var_abuf, values=[20, 40, 80, 150, 500], width=15)
        cb_abuf.grid(row=2, column=1, sticky="e", pady=6)

        # Lip-Sync Filtro aresample
        tk.Label(f, text="Filtro Sincronismo Anti-Deriva:", bg="#1e1e2e", fg="#cdd6f4").grid(row=3, column=0, sticky="w", pady=6)
        self.var_aresample = tk.StringVar(value=self.config.get("aresample_filter", "aresample=async=1:first_pts=0"))
        entry_aresample = tk.Entry(f, textvariable=self.var_aresample, bg="#313244", fg="#cdd6f4", insertbackground="white", width=25)
        entry_aresample.grid(row=3, column=1, sticky="e", pady=6)

    def destroy(self):
        try:
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
            self.unbind_all("<MouseWheel>")
        except Exception:
            pass
        super().destroy()

    def _create_discrete_slider_row(self, parent, label_text, color, var_port, options, test_name, desc_text):
        lbl = tk.Label(parent, text=label_text, bg="#1e1e2e", fg=color, font=("Segoe UI", 9, "bold"))
        lbl.pack(anchor="w", pady=(3, 1))

        frame = tk.Frame(parent, bg="#1e1e2e")
        frame.pack(fill="x", pady=(0, 2))

        # Entry editable directo
        entry = tk.Entry(frame, textvariable=var_port, bg="#313244", fg="#cdd6f4", width=7, font=("Consolas", 10, "bold"), insertbackground="white")
        entry.pack(side="left", padx=(0, 6))

        # Índice más cercano
        curr_val = var_port.get()
        if curr_val in options:
            start_idx = options.index(curr_val)
        else:
            start_idx = min(range(len(options)), key=lambda i: abs(options[i] - curr_val))

        var_idx = tk.IntVar(value=start_idx)

        def on_scale_move(val):
            idx = int(float(val))
            if 0 <= idx < len(options):
                var_port.set(options[idx])

        scale = tk.Scale(
            frame, from_=0, to=len(options)-1, orient="horizontal", variable=var_idx,
            bg="#1e1e2e", fg="#cdd6f4", troughcolor="#313244", highlightthickness=0,
            activebackground=color, showvalue=False, resolution=1, length=240,
            command=on_scale_move
        )
        scale.pack(side="left", padx=4)

        def on_entry_change(*args):
            try:
                v = var_port.get()
                if v in options:
                    var_idx.set(options.index(v))
            except Exception:
                pass

        var_port.trace_add("write", on_entry_change)

        btn_test = tk.Button(
            frame, text="🔍 Probar", bg="#45475a", fg="#cdd6f4", font=("Segoe UI", 8), relief="flat", padx=8, pady=2,
            command=lambda: self._test_port_action(var_port.get(), test_name)
        )
        btn_test.pack(side="left", padx=6)

        lbl_desc = tk.Label(frame, text=desc_text, bg="#1e1e2e", fg="#6c7086", font=("Segoe UI", 8))
        lbl_desc.pack(side="left", padx=2)

    def _build_network_tab(self, parent):
        # Contenedor con Scrollbar vertical para adaptarse a cualquier resolución de pantalla
        canvas = tk.Canvas(parent, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e1e2e")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll con rueda del ratón
        def _on_mousewheel(event):
            if event.num == 5 or event.delta < 0:
                canvas.yview_scroll(2, "units")
            elif event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-2, "units")

        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        f = tk.Frame(scrollable_frame, bg="#1e1e2e")
        f.pack(fill="both", expand=True, padx=15, pady=8)

        # 1. Puerto RX Local con Slider Discreto
        self.var_rx_port = tk.IntVar(value=self.config.get("rx_port", 5200))
        self._create_discrete_slider_row(
            f, "📥 Puerto RX Local (Recepción):", "#a6e3a1", self.var_rx_port,
            [5000, 5002, 5004, 5006, 5010, 5200, 5202, 5204, 5210, 5500, 6002, 7000],
            "Recepción RX", "(Donde esta máquina escucha)"
        )

        # 2. Puerto TX Remoto con Slider Discreto
        self.var_tx_port = tk.IntVar(value=self.config.get("tx_port", 5000))
        self._create_discrete_slider_row(
            f, "📤 Puerto TX Remoto (Transmisión Manual / Fallback):", "#89b4fa", self.var_tx_port,
            [5000, 5002, 5004, 5006, 5010, 5200, 5202, 5204, 5210, 5500, 6002, 7000],
            "Transmisión TX", "(Destino al marcar por IP Manual)"
        )

        # 3. Puerto de Señalización con Slider Discreto
        self.var_sig_port = tk.IntVar(value=self.config.get("signaling_port", 6010))
        self._create_discrete_slider_row(
            f, "🔔 Puerto Señalización / Descubrimiento LAN:", "#f9e2af", self.var_sig_port,
            [6000, 6005, 6010, 6015, 6020, 6025, 6030, 6050],
            "Señalización", "(Descubrimiento y timbrado LAN)"
        )

        # 4. Parámetros de búferes
        frame_buffers = tk.Frame(f, bg="#1e1e2e")
        frame_buffers.pack(fill="x", pady=6)

        tk.Label(frame_buffers, text="Búfer FIFO UDP (Bytes):", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.var_fifo = tk.IntVar(value=self.config.get("fifo_size", 0))
        cb_fifo = ttk.Combobox(frame_buffers, textvariable=self.var_fifo, values=[0, 32768, 50000, 100000], width=8)
        cb_fifo.pack(side="left", padx=(0, 15))

        tk.Label(frame_buffers, text="Búfer Cámara RAM:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.var_rtbuf = tk.StringVar(value=self.config.get("rtbufsize", "250M"))
        cb_rtbuf = ttk.Combobox(frame_buffers, textvariable=self.var_rtbuf, values=["100M", "200M", "250M", "300M", "500M"], width=8)
        cb_rtbuf.pack(side="left")

        # 5. Cuadro explicativo
        tip_frame = tk.Frame(f, bg="#313244", padx=10, pady=6)
        tip_frame.pack(fill="x", pady=(4, 4))
        tip_lbl = (
            "💡 ¿Cómo se selecciona el puerto de transmisión (TX)?\n"
            "• Al llamar a un contacto de la lista, la señalización P2P negocia el puerto automáticamente:\n"
            "  tu TX transmitirá al puerto exacto en el que tu compañero configuró su RX.\n"
            "• Si marcas por 'IP Manual', se transmitirá hacia el 'Puerto TX' configurado arriba.\n"
            "• El slider salta limpiamente entre las opciones de puertos válidos recomendados."
        )
        tk.Label(tip_frame, text=tip_lbl, bg="#313244", fg="#a6adc8", font=("Segoe UI", 8), justify="left").pack(anchor="w")

        # 6. Sección Firewall 1-Clic
        fw_frame = tk.Frame(f, bg="#24273a", padx=10, pady=8, relief="groove", bd=1)
        fw_frame.pack(fill="x", pady=(4, 4))
        
        os_name = "Windows Defender" if self.is_win else "UFW / iptables (Linux / Kali)"
        tk.Label(
            fw_frame, text=f"🛡️ Configuración de Firewall ({os_name})",
            bg="#24273a", fg="#fab387", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 3))
        
        fw_desc = (
            "Abre ÚNICAMENTE los puertos seleccionados arriba (Señalización + RX) en el firewall,\n"
            "sin habilitar puertos innecesarios para garantizar la máxima seguridad de tu equipo."
        )
        tk.Label(fw_frame, text=fw_desc, bg="#24273a", fg="#cdd6f4", font=("Segoe UI", 8), justify="left").pack(anchor="w", pady=(0, 5))

        btn_apply_fw = tk.Button(
            fw_frame, text=" 🛡️ Abrir Puertos Seleccionados en Firewall (1 Clic) ",
            bg="#fab387", fg="#11111b", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=4,
            command=self._apply_firewall_action
        )
        btn_apply_fw.pack(anchor="w")

    def _test_port_action(self, port_val, port_name):
        ok, msg = test_udp_port(port_val)
        if ok:
            messagebox.showinfo("Verificación de Puerto", f"✅ {port_name} (UDP {port_val}):\n\n{msg}")
        else:
            messagebox.showwarning("Verificación de Puerto", f"❌ {port_name} (UDP {port_val}):\n\n{msg}")

    def _apply_firewall_action(self):
        try:
            sig = int(self.var_sig_port.get())
            rx = int(self.var_rx_port.get())
        except Exception:
            messagebox.showerror("Error", "Por favor ingresa puertos numéricos válidos.")
            return

        ok, msg = apply_firewall_rules([sig, rx], self.config)
        if ok:
            messagebox.showinfo("Firewall del Sistema", f"✅ ¡Operación Exitosa!\n\n{msg}")
        else:
            messagebox.showwarning("Firewall del Sistema", f"⚠️ Aviso de Firewall:\n\n{msg}")

    def _save_changes(self):
        # 1. Guardar Hardware Seleccionado
        selected_v_name = self.var_video_choice.get()
        selected_a_name = self.var_audio_choice.get()
        
        v_id = selected_v_name
        for d in self.detected_video:
            if d["display_name"] == selected_v_name:
                v_id = d["ffmpeg_id"]
                break
                
        a_id = selected_a_name
        for d in self.detected_audio:
            if d["display_name"] == selected_a_name:
                a_id = d["ffmpeg_id"]
                break

        if self.is_win:
            self.config["devices"]["windows"]["video"] = v_id
            self.config["devices"]["windows"]["audio"] = a_id
            self.config["devices"]["windows"]["audio_friendly"] = selected_a_name
        else:
            self.config["devices"]["linux"]["video"] = v_id
            self.config["devices"]["linux"]["audio"] = a_id

        # 2. Guardar Video
        self.config["video_bitrate"] = self.var_bitrate.get()
        self.config["video_maxrate"] = self.var_bitrate.get()
        self.config["video_bufsize"] = self.var_bitrate.get()
        self.config["fps"] = int(self.var_fps.get())
        self.config["gop"] = int(self.var_gop.get())
        self.config["preset"] = self.var_preset.get()
        self.config["tune"] = self.var_tune.get()
        self.config["pix_fmt"] = self.var_pix_fmt.get()

        # 3. Guardar Audio
        self.config["audio_codec"] = self.var_acodec.get()
        self.config["audio_bitrate"] = self.var_abitrate.get()
        self.config["audio_buffer_size_ms"] = int(self.var_abuf.get())
        self.config["aresample_filter"] = self.var_aresample.get()

        # 4. Guardar Red
        self.config["signaling_port"] = int(self.var_sig_port.get())
        self.config["rx_port"] = int(self.var_rx_port.get())
        self.config["tx_port"] = int(self.var_tx_port.get())
        self.config["fifo_size"] = int(self.var_fifo.get())
        self.config["rtbufsize"] = self.var_rtbuf.get()

        if save_config(self.config):
            messagebox.showinfo("Configuración", "¡Dispositivos y parámetros guardados exitosamente!")
            if self.on_saved:
                self.on_saved(self.config)
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración.")
