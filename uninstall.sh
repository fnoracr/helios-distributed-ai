#!/bin/bash

# Comprobar si se ejecuta como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Por favor, ejecuta este script con privilegios de administrador (sudo ./uninstall.sh)" >&2
  exit 1
fi

echo ">>> Deteniendo y deshabilitando el servicio del worker..."
systemctl stop helios-worker.service
systemctl disable helios-worker.service

echo ">>> Eliminando el archivo del servicio..."
rm /etc/systemd/system/helios-worker.service
systemctl daemon-reload

echo ">>> Eliminando el directorio de la aplicación en /opt/HeliosAIWorker..."
rm -rf /opt/HeliosAIWorker

echo ">>> Eliminando el acceso directo del escritorio..."
# Busca el usuario real para encontrar su carpeta de aplicaciones
REAL_USER=$(logname)
DESKTOP_FILE="/home/$REAL_USER/.local/share/applications/helios-ai-chat.desktop"
if [ -f "$DESKTOP_FILE" ]; then
    rm "$DESKTOP_FILE"
fi

echo ">>> ¡Desinstalación completada!"