# --- English ---
# # FINAL MULTI-MODAL WORKER - FULLY COMMENTED VERSION #
#
# This is the client application. This script will be compiled into `worker.exe`.
# Users run this on their local machines to connect to the public orchestrator server,
# contribute computing power, and get access to the AI chat.

# --- Español ---
# # WORKER MULTI-MODAL FINAL - VERSIÓN COMPLETAMENTE COMENTADA #
#
# Esta es la aplicación cliente. Este script se compilará en `worker.exe`.
# Los usuarios lo ejecutan en sus ordenadores locales para conectarse al servidor,
# contribuir con su poder de cómputo y obtener acceso al chat de IA.

# -*- coding: utf-8 -*-
import requests
import time
import json
import os
import threading
from transformers import pipeline

# --- English ---
# --- Dependency Imports for File Processing ---
# These are required for the multi-modal capabilities. They are imported here
# to ensure they are included when the script is packaged into an executable.
# --- Español ---
# --- Importaciones de Dependencias para Procesamiento de Archivos ---
# Estas son necesarias para las capacidades multi-modales. Se importan aquí
# para asegurar que se incluyan cuando el script se empaquete en un ejecutable.
try:
    import PyPDF2
    import docx
    from PIL import Image
    import librosa
except ImportError:
    # This error should not occur for the end-user if dependencies are packaged correctly.
    # Este error no debería ocurrir para el usuario final si las dependencias se empaquetan correctamente.
    print("ERROR: Missing dependencies.")
    exit()

# --- English ---
# --- Configuration ---
# --- Español ---
# --- Configuración ---

# ================================ IMPORTANT / IMPORTANTE =================================
# --- English ---
# CHANGE THIS URL to the public IP address or domain of your orchestrator server before compiling.
# --- Español ---
# CAMBIA ESTA URL a la dirección IP pública o dominio de tu servidor orquestador antes de compilar.
ORCHESTRATOR_PUBLIC_URL = "https://api.noragentia.com"
# =========================================================================================

# --- English ---
# Use the APPDATA folder for configuration files to keep the user's system clean.
# This is the standard location for application data on Windows.
# --- Español ---
# Usar la carpeta APPDATA para los archivos de configuración para mantener limpio el sistema del usuario.
# Esta es la ubicación estándar para los datos de aplicación en Windows.
SESSION_FILE = os.path.join(os.getenv('APPDATA'), 'HeliosAIWorker', 'worker_session.json')

# --- English ---
# Self-reported hardware specifications. This could be expanded to be detected automatically.
# --- Español ---
# Especificaciones de hardware auto-reportadas. Esto podría expandirse para ser detectado automáticamente.
WORKER_SPECS = { "gpu": "N/A", "cpu_cores": 8, "memory": "16GB" }

# --- English ---
# Time in seconds between polling for new tasks or sending heartbeats.
# --- Español ---
# Tiempo en segundos entre la solicitud de nuevas tareas o el envío de heartbeats.
POLL_INTERVAL = 5
HEARTBEAT_INTERVAL = 30

# --- English ---
# --- Global state variables ---
# These variables hold the worker's current state, such as the loaded AI model.
# --- Español ---
# --- Variables de estado globales ---
# Estas variables mantienen el estado actual del worker, como el modelo de IA cargado.
expert_pipeline = None
assigned_expert_type = None
stop_heartbeat = threading.Event()

def send_heartbeat(worker_id):
    # --- English ---
    # This function runs in a separate background thread.
    # Its sole purpose is to send a "I'm still alive" signal to the orchestrator
    # every 30 seconds. If the orchestrator doesn't receive these, it will assume
    # the worker has disconnected and will purge it from the active list.
    # --- Español ---
    # Esta función se ejecuta en un hilo separado en segundo plano.
    # Su único propósito es enviar una señal de "sigo vivo" al orquestador
    # cada 30 segundos. Si el orquestador no las recibe, asumirá que el
    # worker se ha desconectado y lo eliminará de la lista de activos.
    while not stop_heartbeat.is_set():
        try:
            requests.post(f"{ORCHESTRATOR_PUBLIC_URL}/heartbeat", json={"worker_id": worker_id})
        except requests.exceptions.RequestException:
            # We use 'pass' to ignore errors, preventing the console from filling up
            # with error messages if the server is temporarily unreachable.
            # Usamos 'pass' para ignorar errores, previniendo que la consola se llene
            # de mensajes de error si el servidor está temporalmente inaccesible.
            pass
        time.sleep(HEARTBEAT_INTERVAL)

def initialize_ai_model(model_info):
    # --- English ---
    # Downloads (if not already cached) and loads the AI model that the
    # orchestrator has assigned to this worker.
    # --- Español ---
    # Descarga (si no está ya en caché) y carga el modelo de IA que el
    # orquestador ha asignado a este worker.
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
    # It handles different file types and AI inference logic.
    # --- Español ---
    # Esta es la función de trabajo principal. Procesa una subtarea basándose en el
    # rol asignado actualmente al worker (ej: "image-captioning").
    # Gestiona diferentes tipos de archivo y la lógica de inferencia de IA.
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
    # registers with the server, creates the session file (the "access pass"),
    # and starts the heartbeat thread.
    # --- Español ---
    # Esta función se ejecuta una vez cuando el worker arranca. Crea el directorio de
    # configuración, se registra en el servidor, crea el archivo de sesión (el "pase de acceso")
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
    # assignment, loads the appropriate model if the role changes, and polls for
    # sub-tasks to process.
    # --- Español ---
    # Este es el bucle operacional principal. Pide continuamente una asignación de rol
    # al servidor, carga el modelo apropiado si el rol cambia, y solicita subtareas
    # para procesar.
    global assigned_expert_type
    while True:
        try:
            # Always check for a new (potentially better) assignment based on network needs.
            # Siempre comprobar si hay una nueva (y potencialmente mejor) asignación basada en las necesidades de la red.
            response = requests.get(f"{ORCHESTRATOR_PUBLIC_URL}/request-assignment/{worker_id}")
            response.raise_for_status()
            assignment = response.json()
            if assigned_expert_type != assignment['assigned_expert']:
                assigned_expert_type = assignment['assigned_expert']
                print(f"Assignment updated: I am now a '{assigned_expert_type}' expert. | Asignación actualizada: ahora soy un experto en '{assigned_expert_type}'.")
                if not initialize_ai_model(assignment['model_info']):
                    assigned_expert_type = None; time.sleep(10); continue
            
            # If assigned a role, look for a task of that type.
            # Si se le ha asignado un rol, buscar una tarea de ese tipo.
            if assigned_expert_type:
                task_response = requests.get(f"{ORCHESTRATOR_PUBLIC_URL}/get-sub-task/{worker_id}/{assigned_expert_type}")
                task_response.raise_for_status()
                sub_task = task_response.json()
                if "id" in sub_task:
                    result = process_sub_task(sub_task)
                    requests.post(f"{ORCHESTRATOR_PUBLIC_URL}/submit-sub-task-result", json={
                        "worker_id": worker_id, "sub_task_id": sub_task['id'], "result": json.dumps(result)
                    })
                else: 
                    # No tasks for my specialty, wait a bit before asking again.
                    # No hay tareas para mi especialidad, esperar un poco antes de volver a preguntar.
                    time.sleep(POLL_INTERVAL)
            else: 
                # Not assigned yet, wait before asking again.
                # Aún no asignado, esperar antes de volver a preguntar.
                time.sleep(10)
        except requests.exceptions.RequestException as e:
            print(f"Communication error: {e}. Retrying... | Error de comunicación: {e}. Reintentando...")
            time.sleep(10)

if __name__ == "__main__":
    worker_id = None
    try:
        # --- Inicio del bloque de captura de errores ---
        try:
            # Este bucle asegura que el worker siga intentando conectarse
            while worker_id is None:
                worker_id = startup_sequence()
                if worker_id is None:
                    print("Could not connect to server. Retrying in 1 minute... | No se pudo conectar al servidor. Reintentando en 1 minuto...")
                    time.sleep(60)

            if worker_id:
                main_loop(worker_id)
        except Exception as e:
            # Si ocurre cualquier error, se muestra aquí
            print("\n" + "="*60)
            print("An unhandled error occurred. | Ha ocurrido un error no controlado.")
            print(f"ERROR: {e}")
            print("The window will close in 60 seconds. | La ventana se cerrará en 60 segundos.")
            print("="*60)
            time.sleep(60)
        # --- Fin del bloque de captura de errores ---
    finally:
        # Este código de limpieza se ejecuta siempre, incluso si hay un error
        stop_heartbeat.set()
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            print(f"\nWorker shutdown. Access pass removed. | Worker apagado. Pase de acceso eliminado.")