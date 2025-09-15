#!/bin/bash

# Comprobar si se ejecuta como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Por favor, ejecuta este script con privilegios de administrador (sudo ./install.sh)" >&2
  exit 1
fi

echo ">>> Creando directorio de instalación en /opt/HeliosAIWorker..."
INSTALL_DIR="/opt/HeliosAIWorker"
mkdir -p $INSTALL_DIR

echo ">>> Copiando archivos de la aplicación..."
cp worker_linux.py $INSTALL_DIR/
cp launch_chat_linux.py $INSTALL_DIR/

echo ">>> Configurando entorno virtual de Python..."
python3 -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate

echo ">>> Instalando dependencias (esto puede tardar varios minutos)..."
pip install requests "transformers[torch]" accelerate PyPDF2 python-docx Pillow librosa huggingface_hub

echo ">>> Configurando el servicio del worker..."
# Reemplaza 'TU_USUARIO' con el usuario que no es root que inició el sudo
REAL_USER=$(logname)
sed "s/User=TU_USUARIO/User=$REAL_USER/" helios-worker.service > /etc/systemd/system/helios-worker.service

systemctl daemon-reload
systemctl enable helios-worker.service
systemctl start helios-worker.service

echo ">>> Creando el acceso directo del escritorio..."
DESKTOP_DIR=$(getent passwd $REAL_USER | cut -d: -f6)/.local/share/applications
mkdir -p $DESKTOP_DIR
cp helios-ai-chat.desktop $DESKTOP_DIR/

echo ">>> ¡Instalación completada!"
echo "Busca 'Helios AI Chat' en el menú de aplicaciones para iniciar la interfaz de chat."