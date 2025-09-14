#!/bin/bash

# --- English ---
# # Helios AI Worker - Linux Installer (Online Version) #
# This script downloads the required Python files from a public URL and installs them.
# It must be run with root privileges (e.g., `sudo bash install.sh`).
# --- Español ---
# # Helios AI Worker - Instalador para Linux (Versión Online) #
# Este script descarga los archivos de Python necesarios desde una URL pública y los instala.
# Debe ejecutarse con privilegios de root (ej: `sudo bash install.sh`).

# --- Configuration ---
# --- English ---
# IMPORTANT: These URLs must point to the "raw" content of your Python files on GitHub.
# --- Español ---
# IMPORTANTE: Estas URLs deben apuntar al contenido "raw" de tus archivos de Python en GitHub.
WORKER_PY_URL="https://raw.githubusercontent.com/fnoracr/helios-distributed-ai/main/worker_linux.py"
LAUNCHER_PY_URL="https://raw.githubusercontent.com/fnoracr/helios-distributed-ai/main/launch_chat_linux.py"

# --- System paths for installation ---
INSTALL_DIR="/opt/HeliosAIWorker"
SERVICE_FILE="/etc/systemd/system/helios-worker.service"
DESKTOP_FILE_TEMPLATE="$HOME/.local/share/applications/helios-chat.desktop"

# --- Functions for colored output ---
print_green() { echo -e "\e[32m$1\e[0m"; }
print_red() { echo -e "\e[31m$1\e[0m"; }

# --- Main Script ---
if [ "$EUID" -ne 0 ]; then
  print_red "Please run this script as root or with sudo. | Por favor, ejecuta este script como root o con sudo."
  exit 1
fi

print_green "Starting Helios AI Worker installation... | Iniciando la instalación de Helios AI Worker..."

echo "-> Updating package lists... | Actualizando lista de paquetes..."
apt-get update -y > /dev/null

echo "-> Installing dependencies (Python, pip)... | Instalando dependencias (Python, pip)..."
apt-get install -y python3 python3-pip python3-venv > /dev/null

echo "-> Creating installation directory... | Creando directorio de instalación..."
mkdir -p $INSTALL_DIR

echo "-> Downloading application scripts... | Descargando scripts de la aplicación..."
if ! curl -sSLo "$INSTALL_DIR/worker.py" "$WORKER_PY_URL" || ! curl -sSLo "$INSTALL_DIR/launch_chat.py" "$LAUNCHER_PY_URL"; then
    print_red "Error: Could not download application files. Check the URLs in the script. | Error: No se pudieron descargar los archivos de la aplicación. Comprueba las URLs en el script."
    exit 1
fi
chmod +x "$INSTALL_DIR/worker.py"
chmod +x "$INSTALL_DIR/launch_chat.py"

echo "-> Installing Python libraries... | Instalando librerías de Python..."
python3 -m pip install requests torch transformers sentencepiece PyPDF2 python-docx Pillow librosa soundfile > /dev/null

echo "-> Configuring auto-start service... | Configurando el servicio de auto-arranque..."
cat << EOF > $SERVICE_FILE
[Unit]
Description=Helios AI Distributed Computing Worker
After=network.target

[Service]
Type=simple
User=$SUDO_USER
ExecStart=/usr/bin/python3 $INSTALL_DIR/worker.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# --- Create desktop launcher as the original user ---
sudo -u $SUDO_USER bash << EOS
echo "-> Creating application launcher... | Creando el lanzador de aplicación..."
DESKTOP_FILE="${DESKTOP_FILE_TEMPLATE/\$HOME/$HOME}"
mkdir -p "\$(dirname "\$DESKTOP_FILE")"
cat << EOF > "\$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Name=Helios AI Chat
Comment=Launch the Helios AI Distributed Network Chat
Exec=/usr/bin/python3 $INSTALL_DIR/launch_chat.py
Icon=utilities-terminal
Terminal=true
Type=Application
Categories=Network;
EOF
chmod +x "\$DESKTOP_FILE"
EOS

echo "-> Enabling and starting the worker service... | Habilitando e iniciando el servicio del worker..."
systemctl daemon-reload
systemctl enable helios-worker.service
systemctl start helios-worker.service

print_green "Installation complete! | ¡Instalación completada!"
print_green "Helios AI Worker is running in the background. | Helios AI Worker se está ejecutando en segundo plano."
print_green "Look for 'Helios AI Chat' in your application menu. | Busca 'Helios AI Chat' en tu menú de aplicaciones."
```

---

### **Paso 3: Crear el Paquete de Distribución (`.tar.gz`)**

Ahora que tu `install.sh` está listo, vamos a crear el paquete que le darás a los usuarios de Linux.

1.  **Crea una carpeta nueva y limpia** en tu ordenador. Por ejemplo, `helios-linux-package`.
2.  **Copia dentro de esa carpeta** solo los archivos que el usuario necesita para instalar y desinstalar:
    * `install.sh` (la versión final con tus URLs de GitHub).
    * `uninstall.sh`.
    * (Opcional pero recomendado) Un archivo `README.txt` con instrucciones simples.
3.  **Abre una terminal y navega hasta esa carpeta** (`cd helios-linux-package`).
4.  **Ejecuta el comando `tar`** para crear el archivo comprimido.

    ```bash
    tar -czvf helios-ai-worker-linux-v1.0.tar.gz install.sh uninstall.sh