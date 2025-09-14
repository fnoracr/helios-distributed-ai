#!/bin/bash

# --- English ---
# Helios AI Worker - Linux Uninstaller
# --- Español ---
# Helios AI Worker - Desinstalador para Linux

# --- Configuration ---
INSTALL_DIR="/opt/HeliosAIWorker"
SERVICE_FILE="/etc/systemd/system/helios-worker.service"
DESKTOP_FILE_TEMPLATE="$HOME/.local/share/applications/helios-chat.desktop"

# --- Functions ---
print_green() { echo -e "\e[32m$1\e[0m"; }
print_red() { echo -e "\e[31m$1\e[0m"; }

# --- Main Script ---
if [ "$EUID" -ne 0 ]; then
  print_red "Por favor, ejecuta este script como root o con sudo."
  exit 1
fi

print_green "Desinstalando Helios AI Worker..."

# --- English ---
# Step 1: Stop and disable the service
# --- Español ---
# Paso 1: Detener y deshabilitar el servicio
echo "-> Deteniendo el servicio del worker..."
systemctl stop helios-worker.service
systemctl disable helios-worker.service

# --- English ---
# Step 2: Remove files
# --- Español ---
# Paso 2: Eliminar archivos
echo "-> Eliminando archivos del sistema..."
rm -f $SERVICE_FILE
rm -rf $INSTALL_DIR

# This part runs as the original user to remove files from their home directory
sudo -u $SUDO_USER bash << EOS
echo "-> Eliminando el lanzador de aplicación..."
DESKTOP_FILE="${DESKTOP_FILE_TEMPLATE/\$HOME/$HOME}"
rm -f "\$DESKTOP_FILE"
EOS

# --- English ---
# Step 3: Reload systemd
# --- Español ---
# Paso 3: Recargar systemd
systemctl daemon-reload

print_green "¡Desinstalación completada!"
```

---

### Cómo Distribuirlo (Guía para Ti)

1.  **Sube tu Código:** Crea un repositorio en GitHub (o similar) y sube las versiones de `worker.py` y `launch_chat.py` con las rutas de Linux.
2.  **Obtén los Enlaces "Raw":** En GitHub, ve a cada archivo y haz clic en el botón "Raw". Copia la URL de la barra de direcciones.
3.  **Actualiza `install.sh`:** Pega esas URLs "raw" en las variables `WORKER_PY_URL` y `LAUNCHER_PY_URL` del script `install.sh`.
4.  **Crea el Paquete:** En tu ordenador, crea una carpeta y mete dentro los archivos `install.sh`, `uninstall.sh` y un `README.md` con las instrucciones para el usuario.
5.  **Comprime el Paquete:** Abre una terminal en esa carpeta y ejecuta:
    ```bash
    tar -czvf helios-ai-worker-linux-v1.0.tar.gz *
    ```
    Esto creará un archivo `helios-ai-worker-linux-v1.0.tar.gz`. ¡Este es tu "instalador" para Linux!

### La Experiencia del Usuario de Linux

Ahora, para instalar tu software, un usuario de Linux solo tendría que hacer lo siguiente en su terminal:

1.  **Descargar el paquete:**
    ```bash
    wget http://tu-sitio-web.com/helios-ai-worker-linux-v1.0.tar.gz
    ```
2.  **Descomprimirlo:**
    ```bash
    tar -xzvf helios-ai-worker-linux-v1.0.tar.gz
    ```
3.  **Ejecutar el instalador:**
    ```bash
    cd helios-ai-worker-linux-v1.0
    sudo bash install.sh