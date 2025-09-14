# --- English ---
# # FINAL CHAT LAUNCHER - LINUX VERSION, FULLY COMMENTED #
#
# This simple script will be the target for the user's desktop launcher file
# (`.desktop`). Its only job is to read the session file created by the worker
# and open the user's unique chat URL in their default web browser.

# --- Español ---
# # LANZADOR DE CHAT FINAL - VERSIÓN LINUX, COMPLETAMENTE COMENTADA #
#
# Este simple script será el objetivo del archivo lanzador de escritorio del
# usuario (`.desktop`). Su único trabajo es leer el archivo de sesión creado
# por el worker y abrir la URL de chat única del usuario en su navegador
# web predeterminado.

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
# This URL MUST MATCH the one in worker.py before packaging.
# --- Español ---
# ESTA URL DEBE COINCIDIR con la del archivo worker.py antes de empaquetar.
ORCHESTRATOR_PUBLIC_URL = "https://api.noragentia.com"
# =========================================================================================

# --- English ---
# The session file is stored in the standard Linux config directory (~/.config).
# `os.path.expanduser('~')` resolves to the user's home directory (e.g., /home/user).
# This path must be identical to the one defined in the Linux worker.py.
# --- Español ---
# El archivo de sesión se guarda en el directorio de configuración estándar de Linux (~/.config).
# `os.path.expanduser('~')` se resuelve al directorio home del usuario (ej: /home/usuario).
# Esta ruta debe ser idéntica a la definida en el worker.py de Linux.
SESSION_FILE = os.path.join(os.path.expanduser('~'), '.config', 'HeliosAIWorker', 'worker_session.json')

def main():
    # --- English ---
    # This message will be visible if the user runs this from a terminal.
    # --- Español ---
    # Este mensaje será visible si el usuario ejecuta esto desde una terminal.
    print("Looking for an active worker session... | Buscando una sesión de worker activa...")

    # --- English ---
    # Wait up to 10 seconds for the worker service to start and create the session file.
    # This handles cases where the user clicks the launcher immediately after a computer restart,
    # before the background worker service has had time to register and create its session file.
    # --- Español ---
    # Esperar hasta 10 segundos a que el servicio del worker arranque y cree el archivo de sesión.
    # Esto gestiona los casos en que el usuario hace clic en el lanzador inmediatamente
    # después de reiniciar el ordenador, antes de que el servicio del worker en segundo plano
    # haya tenido tiempo de registrarse y crear su archivo de sesión.
    for _ in range(10):
        if os.path.exists(SESSION_FILE):
            break
        time.sleep(1)

    if not os.path.exists(SESSION_FILE):
        # --- English ---
        # If the session file is not found after waiting, inform the user.
        # --- Español ---
        # Si el archivo de sesión no se encuentra después de esperar, informar al usuario.
        print("Error: Active worker session not found. | Error: No se encontró la sesión del worker.")
        print("Please ensure the Helios AI Worker service is running. | Por favor, asegúrate de que el servicio Helios AI Worker se está ejecutando.")
        time.sleep(5) # Keep the window open for a few seconds so the user can read the message. | Mantener la ventana abierta unos segundos para que el usuario lea el mensaje.
        return

    try:
        # --- English ---
        # Read the worker ID from the JSON session file.
        # --- Español ---
        # Leer el ID del worker desde el archivo de sesión JSON.
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
            worker_id = data.get("worker_id")

        if worker_id:
            # --- English ---
            # Construct the user's unique chat URL and open it in the default web browser.
            # --- Español ---
            # Construir la URL de chat única del usuario y abrirla en el navegador web predeterminado.
            chat_url = f"{ORCHESTRATOR_PUBLIC_URL}/?worker_id={worker_id}"
            print(f"Opening chat URL: {chat_url} | Abriendo URL de chat: {chat_url}")
            webbrowser.open(chat_url)
        else:
            print("Error: The session file is invalid or does not contain a worker ID. | Error: El archivo de sesión es inválido o no contiene un ID de worker.")
            time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e} | Ha ocurrido un error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    # --- English ---
    # This is the entry point of the script. It calls the main function.
    # --- Español ---
    # Este es el punto de entrada del script. Llama a la función principal.
    main()