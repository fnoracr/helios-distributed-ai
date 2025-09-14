#!/bin/bash

# --- English ---
# Helios AI Worker - Linux Installer
# This script must be run with root privileges (e.g., sudo bash install.sh)
# --- Español ---
# Helios AI Worker - Instalador para Linux
# Este script debe ejecutarse con privilegios de root (ej: sudo bash install.sh)

# --- Configuration ---
# --- English ---
# IMPORTANT: Before distributing, you must upload your Python files
# and change these URLs to point to their raw content links.
# --- Español ---
# IMPORTANTE: Antes de distribuir, debes subir tus archivos de Python
# y cambiar estas URLs para que apunten a sus enlaces de contenido raw.
WORKER_PY_URL="https://raw.githubusercontent.com/tu-usuario/tu-repo/main/worker.py"
LAUNCHER_PY_URL="https://raw.githubusercontent.com/tu-usuario/tu-repo/main/launch_chat.py"

INSTALL_DIR="/opt/HeliosAIWorker"
CONFIG_DIR_TEMPLATE="$HOME/.config/HeliosAIWorker" # For the user running the installer
SERVICE_FILE="/etc/systemd/system/helios-worker.service"
DESKTOP_FILE_TEMPLATE="$HOME/.local/share/applications/helios-chat.desktop"

# --- Functions ---
print_green() { echo -e "\e[32m$1\e[0m"; }
print_red() { echo -e "\e[31m$1\e[0m"; }

# --- Main Script ---
# --- English ---
# Check for root privileges
# --- Español ---
# Comprobar privilegios de root
if [ "$EUID" -ne 0 ]; then
  print_red "Por favor, ejecuta este script como root o con sudo."
  exit 1
fi

print_green "Iniciando la instalación de Helios AI Worker..."

# --- English ---
# Step 1: Create directories
# --- Español ---
# Paso 1: Crear directorios
echo "-> Creando directorio de instalación en $INSTALL_DIR..."
mkdir -p $INSTALL_DIR

# --- English ---
# Step 2: Download the worker and launcher scripts
# --- Español ---
# Paso 2: Descargar los scripts del worker y el lanzador
echo "-> Descargando scripts de la aplicación..."
curl -sSLo "$INSTALL_DIR/worker.py" "$WORKER_PY_URL"
curl -sSLo "$INSTALL_DIR/launch_chat.py" "$LAUNCHER_PY_URL"
chmod +x "$INSTALL_DIR/worker.py"
chmod +x "$INSTALL_DIR/launch_chat.py"

# --- English ---
# Step 3: Create the systemd service file for auto-start
# --- Español ---
# Paso 3: Crear el archivo de servicio de systemd para el auto-arranque
echo "-> Configurando el servicio de auto-arranque..."
cat << EOF > $SERVICE_FILE
[Unit]
Description=Helios AI Distributed Computing Worker
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/worker.py
Restart=on-failure
RestartSec=10
User=$SUDO_USER

[Install]
WantedBy=multi-user.target
EOF

# --- English ---
# Step 4: Create the desktop launcher for the current user
# --- Español ---
# Paso 4: Crear el lanzador de escritorio para el usuario actual
# This part runs as the original user to place files in their home directory
sudo -u $SUDO_USER bash << EOS
echo "-> Creando el lanzador de aplicación..."
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

# --- English ---
# Step 5: Enable and start the service
# --- Español ---
# Paso 5: Habilitar e iniciar el servicio
echo "-> Habilitando e iniciando el servicio del worker..."
systemctl daemon-reload
systemctl enable helios-worker.service
systemctl start helios-worker.service

print_green "¡Instalación completada!"
print_green "Helios AI Worker se está ejecutando en segundo plano."
print_green "Busca 'Helios AI Chat' en tu menú de aplicaciones para empezar."
