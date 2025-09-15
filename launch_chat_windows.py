# --- English ---
# # FINAL CHAT LAUNCHER - FULLY COMMENTED VERSION #
#
# This simple script will be compiled into `launch_chat.exe` and will
# be the target for the user's desktop shortcut.
# Its only job is to read the session file created by the worker and open
# the user's unique chat URL in their default web browser.

# --- Español ---
# # LANZADOR DE CHAT FINAL - VERSIÓN COMPLETAMENTE COMENTADA #
#
# Este simple script se compilará en `launch_chat.exe` y será el
# objetivo del acceso directo del escritorio del usuario.
# Su único trabajo es leer el archivo de sesión creado por el worker y abrir
# la URL de chat única del usuario en su navegador web predeterminado.

# -*- coding: utf-8 -*-
import json
import os
import webbrowser
import time

# --- English ---
# --- Configuration ---
# --- Español ---
# --- Configuración ---

# ================================ IMPORTANT / IMPORTANTE =================================
# --- English ---
# This URL MUST MATCH the one in worker.py before compiling.
# --- Español ---
# ESTA URL DEBE COINCIDIR con la del archivo worker.py antes de compilar.
ORCHESTRATOR_PUBLIC_URL = "https://api.noragentia.com"
# =========================================================================================

# --- English ---
# The session file is stored in the standard APPDATA folder to keep the system clean.
# This path must be identical to the one defined in worker.py.
# --- Español ---
# El archivo de sesión se guarda en la carpeta estándar APPDATA para mantener limpio el sistema.
# Esta ruta debe ser idéntica a la definida en worker.py.
SESSION_FILE = os.path.join(os.getenv('APPDATA'), 'HeliosAIWorker', 'worker_session.json')

def main():
    # --- Inicio del bloque de captura de errores ---
    try:
        print("Looking for an active worker session... | Buscando una sesión de worker activa...")

        # Esperar hasta 10 segundos a que el worker cree el archivo de sesión.
        for _ in range(10):
            if os.path.exists(SESSION_FILE):
                break
            time.sleep(1)

        if not os.path.exists(SESSION_FILE):
            # Si no se encuentra el archivo, lanzamos un error para ser capturado abajo.
            raise FileNotFoundError("Active worker session not found. Please ensure the worker is running.")

        # Leer el ID del worker desde el archivo de sesión.
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
            worker_id = data.get("worker_id")

        if worker_id:
            # Construir la URL y abrirla en el navegador.
            chat_url = f"{ORCHESTRATOR_PUBLIC_URL}/?worker_id={worker_id}"
            print(f"Opening chat URL: {chat_url} | Abriendo URL de chat: {chat_url}")
            webbrowser.open(chat_url)
            print("Success! You can close this window now. | ¡Éxito! Ya puedes cerrar esta ventana.")
            time.sleep(10) # Pausa para que el usuario pueda leer el mensaje de éxito.
        else:
            # Si el archivo no tiene un ID, lanzamos un error.
            raise ValueError("The session file is invalid or does not contain a worker ID.")

    except Exception as e:
        # Si ocurre cualquier error durante el proceso, se captura y muestra aquí.
        print("\n" + "="*60)
        print("An error occurred in the launcher. | Ha ocurrido un error en el lanzador.")
        print(f"ERROR: {e}")
        print("Press Enter to close the window. | Presiona Enter para cerrar la ventana.")
        print("="*60)
        input() # Espera a que el usuario presione Enter.
    # --- Fin del bloque de captura de errores ---

if __name__ == "__main__":
    # --- English ---
    # This is the entry point of the script. It calls the main function.
    # --- Español ---
    # Este es el punto de entrada del script. Llama a la función principal.
    main()