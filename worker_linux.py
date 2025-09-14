# --- English ---
# # FINAL MULTI-MODAL WORKER - LINUX VERSION, FULLY COMMENTED #
#
# This is the client application adapted for Linux systems. The `install.sh` script
# will download this file and configure it to run as a background service.
#
# HOW TO PREPARE FOR LINUX PACKAGE:
# 1. IMPORTANT: Change the ORCHESTRATOR_PUBLIC_URL variable below.
# 2. Upload this file to a public URL (like a raw GitHub link) so the installer can fetch it.

# --- Español ---
# # WORKER MULTI-MODAL FINAL - VERSIÓN LINUX, COMPLETAMENTE COMENTADA #
#
# Esta es la aplicación cliente adaptada para sistemas Linux. El script `install.sh`
# descargará este archivo y lo configurará para que se ejecute como un servicio en segundo plano.
#
# CÓMO PREPARAR PARA EL PAQUETE DE LINUX:
# 1. IMPORTANTE: Cambia la variable ORCHESTRATOR_PUBLIC_URL de abajo.
# 2. Sube este archivo a una URL pública (como un enlace raw de GitHub) para que el instalador pueda descargarlo.

# -*- coding: utf-8 -*-
import requests
import time
import json
import os
import threading
from transformers import pipeline

# --- English ---
# --- Dependency Imports for File Processing ---
# These are required for the multi-modal capabilities.
# --- Español ---
# --- Importaciones de Dependencias para Procesamiento de Archivos ---
# Estas son necesarias para las capacidades multi-modales.
try:
    import PyPDF2
    import docx
    from PIL import Image
    import librosa
except ImportError:
    # This error should not occur for the end-user as the installer should handle dependencies.
    # Este error no debería ocurrir para el usuario final ya que el instalador debería gestionar las dependencias.
    print("ERROR: Missing dependencies.")
    exit()

# --- English ---
# --- Configuration ---
# --- Español ---
# --- Configuración ---

# ================================ IMPORTANT / IMPORTANTE =================================
# --- English ---
# CHANGE THIS URL to the public IP address or domain of your orchestrator server before packaging.
# --- Español ---
# CAMBIA ESTA URL a la dirección IP pública o dominio de tu servidor orquestador antes de empaquetar.
ORCHESTRATOR_PUBLIC_URL = "https://api.noragentia.com"
# =========================================================================================

# --- English ---
# Use the standard Linux config directory (~/.config) for the session file.
# `os.path.expanduser('~')` resolves to the user's home directory (e.g., /home/user).
# --- Español ---
# Usar el directorio de configuración estándar de Linux (~/.config) para el archivo de sesión.
# `os.path.expanduser('~')` se resuelve al directorio home del usuario (ej: /home/usuario).
SESSION_FILE = os.path.join(os.path.expanduser('~'), '.config', 'HeliosAIWorker', 'worker_session.json')

# --- English ---
# Self-reported hardware specifications.
# --- Español ---
# Especificaciones de hardware auto-reportadas.
WORKER_SPECS = { "gpu": "N/A", "cpu_cores": 8, "memory": "16GB" }

# --- English ---
# Time in seconds between polling for new tasks or sending heartbeats.
# --- Español ---
# Tiempo en segundos entre la solicitud de nuevas tareas o el envío de heartbeats.
POLL_INTERVAL = 5
HEARTBEAT_INTERVAL = 30

# --- English ---
# --- Global state variables ---
# These variables hold the worker's current state.
# --- Español ---
# --- Variables de estado globales ---
# Estas variables mantienen el estado actual del worker.
expert_pipeline = None
assigned_expert_type = None
stop_heartbeat = threading.Event()

def send_heartbeat(worker_id):
    # --- English ---
    # This function runs in a separate background thread.
    # It sends a "I'm still alive" signal to the orchestrator every 30 seconds.
    # If the orchestrator doesn't receive these, it will purge the worker.
    # --- Español ---
    # Esta función se ejecuta en un hilo separado en segundo plano.
    # Envía una señal de "sigo vivo" al orquestador cada 30 segundos.
    # Si el orquestador no las recibe, eliminará al worker.
    while not stop_heartbeat.is_set():
        try:
            requests.post(f"{ORCHESTRATOR_PUBLIC_URL}/heartbeat", json={"worker_id": worker_id})
        except requests.exceptions.RequestException:
            pass
        time.sleep(HEARTBEAT_INTERVAL)

def initialize_ai_model(model_info):
    # --- English ---
    # Downloads (if not already cached) and loads the AI model assigned by the orchestrator.
    # --- Español ---
    # Descarga (si no está ya en caché) y carga el modelo de IA asignado por el orquestador.
    global expert_pipeline
    print(f"Initializing AI model for '{model_info['task']}'... | Inicializando modelo de IA para '{model_info['task']}'...")
    try:
        expert_pipeline = pipeline(model_info['task'], model=model_info['model'])
        print(f"Model '{model_info['model']}' loaded successfully. | Modelo '{model_info['model']}' cargado con éxito.")
        return True
    except Exception as e:
        print(f"Error loading AI model: {e} | Error al cargar el modelo de IA: {e}")
        return False

def process_sub_task(sub_task):
    # --- English ---
    # This is the core work function. It processes a sub-task based on the
    # worker's currently assigned role (e.g., "image-captioning").
    # --- Español ---
    # Esta es la función de trabajo principal. Procesa una subtarea basándose en el
    # rol asignado actualmente al worker (ej: "image-captioning").
    if not expert_pipeline: return {"error": "AI model not available."}
    task_data = json.loads(sub_task['data'])
    try:
        print(f"Processing '{assigned_expert_type}' sub-task {sub_task['id']}... | Procesando subtarea de '{assigned_expert_type}' {sub_task['id']}...")
        if assigned_expert_type == "document-summarization":
            file_path = task_data['file_path']
            text = ""
            if file_path.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages: text += page.extract_text() + "\n"
            elif file_path.endswith('.docx'):
                doc = docx.Document(file_path)
                for para in doc.paragraphs: text += para.text + "\n"
            if not text.strip(): return {"summary_text": "Document is empty or text could not be extracted."}
            return expert_pipeline(text, min_length=10, max_length=150)[0]
        elif assigned_expert_type == "image-captioning":
            image = Image.open(task_data['file_path'])
            return expert_pipeline(image)[0]
        elif assigned_expert_type == "audio-transcription":
            return expert_pipeline(task_data['file_path'])
        elif assigned_expert_type == "summarization":
            return expert_pipeline(task_data['text'], min_length=5, max_length=30)[0]
        elif assigned_expert_type == "text-generation":
            return expert_pipeline(task_data['text'], max_length=50, num_return_sequences=1)[0]
        else:
            return {"error": "Unknown expert type for processing."}
    except Exception as e:
        print(f"ERROR during processing: {e} | ERROR durante el procesamiento: {e}")
        return {"error": str(e)}

def startup_sequence():
    # --- English ---
    # This function runs once when the worker starts. It creates the config directory,
    # registers with the server, creates the session file, and starts the heartbeat thread.
    # --- Español ---
    # Esta función se ejecuta una vez cuando el worker arranca. Crea el directorio de
    # configuración, se registra en el servidor, crea el archivo de sesión
    # e inicia el hilo del heartbeat.
    global assigned_expert_type
    
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    
    print("Registering with the orchestrator... | Registrándose en el orquestador...")
    try:
        response = requests.post(f"{ORCHESTRATOR_PUBLIC_URL}/register", json={"specs": WORKER_SPECS})
        response.raise_for_status()
        worker_id = response.json()['worker_id']
        with open(SESSION_FILE, 'w') as f: json.dump({"worker_id": worker_id}, f)
        print("\n" + "="*60)
        print("✅ Worker is ACTIVE. You can now use the chat interface! | ✅ Worker ACTIVO. ¡Ya puedes usar la interfaz de chat!")
        print(f"   Open this URL in your browser: | Abre esta URL en tu navegador:")
        print(f"   {ORCHESTRATOR_PUBLIC_URL}/?worker_id={worker_id}")
        print("="*60 + "\n")
    except requests.exceptions.RequestException as e:
        print(f"Error registering: {e} | Error al registrarse: {e}"); return None
    
    heartbeat_thread = threading.Thread(target=send_heartbeat, args=(worker_id,))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()
    print("Waiting for task assignment... | Esperando asignación de tarea...")
    return worker_id

def main_loop(worker_id):
    # --- English ---
    # This is the main operational loop. It continuously asks the server for a role
    # assignment, loads the appropriate model, and polls for sub-tasks to process.
    # --- Español ---
    # Este es el bucle operacional principal. Pide continuamente una asignación de rol
    # al servidor, carga el modelo apropiado, y solicita subtareas para procesar.
    global assigned_expert_type
    while True:
        try:
            response = requests.get(f"{ORCHESTRATOR_PUBLIC_URL}/request-assignment/{worker_id}")
            response.raise_for_status()
            assignment = response.json()
            if assigned_expert_type != assignment['assigned_expert']:
                assigned_expert_type = assignment['assigned_expert']
                print(f"Assignment updated: I am now a '{assigned_expert_type}' expert. | Asignación actualizada: ahora soy un experto en '{assigned_expert_type}'.")
                if not initialize_ai_model(assignment['model_info']):
                    assigned_expert_type = None; time.sleep(10); continue
            
            if assigned_expert_type:
                task_response = requests.get(f"{ORCHESTRATOR_PUBLIC_URL}/get-sub-task/{worker_id}/{assigned_expert_type}")
                task_response.raise_for_status()
                sub_task = task_response.json()
                if "id" in sub_task:
                    result = process_sub_task(sub_task)
                    requests.post(f"{ORCHESTRATOR_PUBLIC_URL}/submit-sub-task-result", json={
                        "worker_id": worker_id, "sub_task_id": sub_task['id'], "result": json.dumps(result)
                    })
                else: time.sleep(POLL_INTERVAL)
            else: time.sleep(10)
        except requests.exceptions.RequestException as e:
            print(f"Communication error: {e}. Retrying... | Error de comunicación: {e}. Reintentando...")
            time.sleep(10)

if __name__ == "__main__":
    worker_id = None
    try:
        # --- English ---
        # This loop ensures the worker keeps trying to connect even if the server is down on startup.
        # --- Español ---
        # Este bucle asegura que el worker siga intentando conectarse aunque el servidor esté caído al arrancar.
        while worker_id is None:
            worker_id = startup_sequence()
            if worker_id is None:
                print("Could not connect to server. Retrying in 1 minute... | No se pudo conectar al servidor. Reintentando en 1 minuto...")
                time.sleep(60)

        if worker_id:
            main_loop(worker_id)
    finally:
        # --- English ---
        # Cleanup: This code runs when the program is closed (e.g., Ctrl+C).
        # It stops the heartbeat thread and removes the session file.
        # --- Español ---
        # Limpieza: Este código se ejecuta cuando el programa se cierra (ej: Ctrl+C).
        # Detiene el hilo del heartbeat y elimina el archivo de sesión.
        stop_heartbeat.set()
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            print(f"\nWorker shutdown. Access pass removed. | Worker apagado. Pase de acceso eliminado.")