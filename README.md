# MeetLAN - Sistema de Videollamada P2P en Tiempo Real (Tipo Zoom / WhatsApp)

**Asignatura:** Comunicaciones Multimedia  
**Facultad:** Facultad de Ingeniería, Universidad de Cuenca  
**Estudiante:** Jose Guaman  
**Plataformas Soportadas:** Windows 10/11 y GNU/Linux Ubuntu  

---

## 1. Descripción del Sistema

**MeetLAN** es una aplicación completa de videoconferencia interactiva diseñada para operar directamente en una red de área local (LAN) bajo arquitectura Peer-to-Peer (P2P), sin requerir servidores externos ni servicios en la nube. 

Incorpora todos los hallazgos y optimizaciones de latencia ultrabaja desarrollados en el **Trabajo en Clase 7 (TC7)** y el **Examen Interciclo**:
* **Compresión de Video:** Códec H.264 (`libx264`) con aceleración vectorial SIMD AVX en espacio `yuv420p`, `preset ultrafast` y `tune zerolatency`.
* **Compresión de Audio:** Códec AAC mono a 64 kbps con filtrado `aresample` anti-deriva y búfer de 40 ms para dispositivos Bluetooth y DirectShow.
* **Transporte Multimedia:** Datagramas MPEG-TS sobre UDP (`pkt_size=1316`, `muxdelay 0`, `flush_packets 1`, `fifo_size=0`).
* **Visualización Picture-in-Picture (PiP):** Presentación idéntica a WhatsApp Video / Zoom: el flujo remoto del compañero ocupa la pantalla de fondo, mientras que la cámara local propia se previsualiza en una miniatura flotante en la **esquina inferior izquierda**.
* **Descubrimiento Automático en LAN:** Saludo inicial por broadcast/sondeo P2P: solo las computadoras con MeetLAN se descubren y aparecen en la lista de contactos.
* **Control de Llamadas con Timbre Audible:** Tono senoidal de repique de llamada (880 Hz) con confirmación obligatoria: **la llamada únicamente inicia si el destinatario presiona "Aceptar"**.

---

## 2. Instalación y Ejecución

### En Windows:
1. Asegúrate de tener instalado Python 3 y FFmpeg (añadido al PATH).
2. Simplemente haz doble clic sobre:
   ```cmd
   run_meetlan.bat
   ```
   *(O desde PowerShell / CMD: `python main.py`)*.

### En Ubuntu / GNU/Linux:
1. Abre una terminal en la carpeta `MeetLAN` e instala las dependencias:
   ```bash
   chmod +x install_ubuntu.sh run_meetlan.sh
   ./install_ubuntu.sh
   ```
2. Ejecuta la aplicación:
   ```bash
   ./run_meetlan.sh
   ```

---

## 3. Módulos y Arquitectura del Software

```text
MeetLAN/
├── main.py              # Punto de entrada de la aplicación
├── config.py            # Gestión y persistencia de parámetros en config.json
├── signaling.py         # Protocolo de señalización y descubrimiento UDP en LAN
├── audio_alert.py       # Motor de timbrado y alerta audible (880 Hz)
├── engine.py            # Orquestador multimedia FFmpeg/FFplay con split y PiP
├── ui_main.py           # Dashboard principal con lista de contactos y estado
├── ui_config.py         # Panel gráfico de configuración de todos los parámetros
├── ui_call.py           # Barra flotante de control de llamada en curso
├── run_meetlan.bat      # Lanzador para Windows
├── run_meetlan.sh       # Lanzador para Linux
├── install_ubuntu.sh    # Instalador de paquetes en Linux
└── config.json          # Archivo generado con las preferencias del usuario
```

---

## 4. Funcionamiento Paso a Paso

### 1. Menú Principal y Descubrimiento P2P
* Al abrir MeetLAN en tu equipo y en el de tu compañero, la aplicación envía un saludo UDP inicial (`DISCOVERY_PING`) en el puerto 6000.
* Ambos equipos se reconocen automáticamente y aparecen en la lista con su **Nombre, Dirección IP y Estado** (🟢 Disponible / 🔴 En llamada).
* También dispones de una casilla para marcar directamente una dirección IP específica.

### 2. Panel de Configuración
Haciendo clic en **"⚙️ Configuración"**, puedes modificar en tiempo real:
* **Video:** Bitrate (`300k`, `500k`, etc.), FPS (`24`, `30`), GoP, Preset (`ultrafast`), Tune (`zerolatency`), Espacio de color (`yuv420p`), Resolución.
* **Audio:** Códec (`aac`), Tasa (`64k`), Búfer de hardware (`40 ms` para Bluetooth), filtro `aresample`.
* **Red / Puertos:** Puerto de Señalización (6000/6050), Puerto RX Local (5000/5001), Puerto TX Remoto (5001/5000), Búfer FIFO (0).
* **Hardware:** Selección de dispositivo de video (Cámara) y audio (Micrófono DirectShow en Windows o PulseAudio en Linux).

### 3. Flujo de Llamada (Aceptación / Rechazo Obligatorio)
1. Presionas **"📞 Llamar"** al lado del contacto deseado.
2. En la pantalla del receptor suena inmediatamente el tono de repique audible de 880 Hz y se despliega la ventana modal:
   * **`[ ✔️ Aceptar ]`**: Detiene el timbre, envía la confirmación de aceptación y arranca la videollamada interactiva en ambas computadoras.
   * **`[ ✖️ Rechazar ]`**: Detiene el timbre, notifica al emisor que la llamada fue declinada y nadie inicia transmisión.
3. Si un usuario ya está en una llamada, responde automáticamente con estado ocupado.

### 4. Durante la Videollamada
* **Fondo:** Se abre la ventana en tiempo real con el video y audio de tu compañero.
* **Esquina Inferior Izquierda:** Aparece la miniatura flotante con tu propia cámara (PiP), permitiéndote verificar tu encuadre tal como en WhatsApp Video.
* **Barra Flotante:** Un panel compacto te muestra la duración de la llamada y el botón **"🔴 Colgar Videollamada"**, el cual detiene de inmediato los procesos en ambos extremos de la conexión.
