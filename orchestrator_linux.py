# --- English ---
# # FINAL, COMPLETE, AND SECURE ORCHESTRATOR (BILINGUAL VERSION) #
#
# This file contains ALL necessary endpoints and logic for the secure,
# reputation-based network. This is the definitive version.
# All comments are provided in English and Spanish.
#
# HOW TO RUN:
# 1. Change the ORCHESTRATOR_PUBLIC_URL in the worker and submit_job files.
# 2. Run on a public server using a production setup (e.g., Gunicorn + NGINX).
# 3. For local testing: uvicorn orchestrator:app --host 0.0.0.0 --port 8000

# --- Español ---
# # ORQUESTADOR FINAL, COMPLETO Y SEGURO (VERSIÓN BILINGÜE) #
#
# Este archivo contiene TODOS los endpoints y la lógica necesarios para la red
# segura, basada en reputación. Esta es la versión definitiva.
# Todos los comentarios están en Inglés y Español.
#
# CÓMO EJECUTAR:
# 1. Cambia la ORCHESTRATOR_PUBLIC_URL en los archivos del worker y de submit_job.
# 2. Ejecútalo en un servidor público usando un setup de producción (ej: Gunicorn + NGINX).
# 3. Para pruebas locales: uvicorn orchestrator:app --host 0.0.0.0 --port 8000

# -*- coding: utf-8 -*-

import uuid
import json
import sqlite3
import time
import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional
from fastapi.responses import HTMLResponse

# --- English ---
# --- Configuration ---
# --- Español ---
# --- Configuración ---
DB_FILE = "orchestrator_secure.db"
REPUTATION_THRESHOLD_TO_SUBMIT = 5.0 # A worker needs this much reputation to allow its user to submit jobs. | La reputación que un worker necesita para que su usuario pueda enviar trabajos.
HEARTBEAT_TIMEOUT_SECONDS = 120 # Workers that are silent for longer than this (in seconds) are purged. | Los workers que no se comunican durante este tiempo (en segundos) son eliminados.
UPLOAD_DIRECTORY = "uploads"
SUPPORTED_EXPERTS = {
    "summarization": {"model": "t5-small", "task": "summarization"},
    "text-generation": {"model": "gpt2", "task": "text-generation"},
    "document-summarization": {"model": "t5-small", "task": "summarization"},
    "image-captioning": {"model": "Salesforce/blip-image-captioning-large", "task": "image-to-text"},
    "audio-transcription": {"model": "openai/whisper-tiny.en", "task": "automatic-speech-recognition"}
}

def get_db_connection():
    # --- English ---
    # Establishes a connection to the SQLite database.
    # --- Español ---
    # Establece una conexión con la base de datos SQLite.
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # --- English ---
    # Initializes the database schema if the tables do not exist.
    # --- Español ---
    # Inicializa el esquema de la base de datos si las tablas no existen.
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            assigned_expert TEXT,
            specs TEXT NOT NULL,
            status TEXT NOT NULL,
            reputation REAL NOT NULL,
            last_heartbeat INTEGER NOT NULL
        )
    ''')
    conn.execute('''CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, prompt TEXT, status TEXT, final_result TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sub_tasks (id TEXT PRIMARY KEY, job_id TEXT, expert_type TEXT, data TEXT, status TEXT, assigned_worker_id TEXT, result TEXT, FOREIGN KEY (job_id) REFERENCES jobs (id))''')
    conn.commit()
    conn.close()

async def purge_inactive_workers():
    # --- English ---
    # Background task that runs periodically to remove workers that haven't sent a heartbeat.
    # --- Español ---
    # Tarea en segundo plano que se ejecuta periódicamente para eliminar workers que no han enviado un heartbeat.
    while True:
        await asyncio.sleep(60) # Run every minute | Ejecutar cada minuto
        timeout_threshold = int(time.time()) - HEARTBEAT_TIMEOUT_SECONDS
        conn = get_db_connection()
        cursor = conn.cursor()
        inactive_ids_tuples = cursor.execute("SELECT id FROM workers WHERE last_heartbeat < ?", (timeout_threshold,)).fetchall()
        
        if inactive_ids_tuples:
            inactive_ids = [row['id'] for row in inactive_ids_tuples]
            print(f"👻 Purging {len(inactive_ids)} inactive worker(s): {inactive_ids}")
            
            placeholders = ', '.join('?' for _ in inactive_ids)
            conn.execute(f"DELETE FROM workers WHERE id IN ({placeholders})", inactive_ids)
            conn.commit()
        conn.close()

app = FastAPI(title="Secure AI Orchestrator | Orquestador de IA Seguro", version="10.0.0")

@app.on_event("startup")
async def on_startup():
    # --- English ---
    # On server startup, initialize the database and start the background task.
    # --- Español ---
    # Al iniciar el servidor, inicializa la base de datos y la tarea en segundo plano.
    init_db()
    asyncio.create_task(purge_inactive_workers())

# --- Pydantic Models ---
class WorkerSpecs(BaseModel): gpu: str; cpu_cores: int; memory: str
class WorkerRegistrationPayload(BaseModel): specs: WorkerSpecs
class JobPayload(BaseModel): prompt: str; worker_id: str
class SubTaskResultPayload(BaseModel): worker_id: str; sub_task_id: str; result: str
class HeartbeatPayload(BaseModel): worker_id: str

# --- API Endpoints ---
@app.post("/register")
def register_worker(payload: WorkerRegistrationPayload):
    # --- English ---
    # Registers a new worker in the system with an initial reputation of 0.
    # --- Español ---
    # Registra un nuevo worker en el sistema con una reputación inicial de 0.
    worker_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute("INSERT INTO workers (id, specs, status, reputation, last_heartbeat) VALUES (?, ?, ?, ?, ?)",
                 (worker_id, json.dumps(payload.specs.dict()), "pending_assignment", 0.0, int(time.time())))
    conn.commit()
    conn.close()
    print(f"✅ Worker registered: {worker_id} with Reputation 0.0")
    return {"status": "success", "worker_id": worker_id}

@app.post("/heartbeat")
def heartbeat(payload: HeartbeatPayload):
    # --- English ---
    # Receives a heartbeat from a worker to keep it active in the network.
    # --- Español ---
    # Recibe un heartbeat de un worker para mantenerlo activo en la red.
    conn = get_db_connection()
    result = conn.execute("UPDATE workers SET last_heartbeat = ? WHERE id = ?", (int(time.time()), payload.worker_id))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Worker not found, might have been purged. Please re-register.")
    return {"status": "acknowledged"}

@app.post("/upload-and-submit-job")
async def upload_and_submit_job(worker_id: str = Form(...), prompt: str = Form(""), file: Optional[UploadFile] = File(None)):
    # --- English ---
    # Accepts a new job (text or file) if the associated worker has enough reputation.
    # --- Español ---
    # Acepta un nuevo trabajo (texto o archivo) si el worker asociado tiene suficiente reputación.
    conn = get_db_connection()
    worker = conn.execute("SELECT reputation FROM workers WHERE id = ?", (worker_id,)).fetchone()
    if not worker: raise HTTPException(status_code=403, detail="Invalid or purged Worker ID. | ID de Worker inválido o purgado.")
    if worker['reputation'] < REPUTATION_THRESHOLD_TO_SUBMIT: raise HTTPException(status_code=403, detail=f"Worker reputation ({worker['reputation']:.1f}) is too low. | La reputación del worker ({worker['reputation']:.1f}) es demasiado baja.")

    job_id = str(uuid.uuid4())
    final_prompt = prompt
    expert_type, file_path = None, None
    
    if file:
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension in ['.pdf', '.docx']: expert_type = 'document-summarization'
        elif file_extension in ['.png', '.jpg', '.jpeg']: expert_type = 'image-captioning'
        elif file_extension in ['.mp3', '.wav', '.flac']: expert_type = 'audio-transcription'
        else: raise HTTPException(status_code=400, detail="Unsupported file type. | Tipo de archivo no soportado.")
        file_path = os.path.join(UPLOAD_DIRECTORY, f"{job_id}{file_extension}")
        with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        final_prompt = f"Processing file: {file.filename}. {prompt}"

    conn.execute("INSERT INTO jobs (id, prompt, status) VALUES (?, ?, ?)", (job_id, final_prompt, "pending"))
    if expert_type and file_path:
        conn.execute("INSERT INTO sub_tasks (id, job_id, expert_type, data, status) VALUES (?, ?, ?, ?, ?)",
                     (str(uuid.uuid4()), job_id, expert_type, json.dumps({"file_path": file_path}), "pending"))
    elif prompt:
        for et in ["summarization", "text-generation"]:
            conn.execute("INSERT INTO sub_tasks (id, job_id, expert_type, data, status) VALUES (?, ?, ?, ?, ?)",
                         (str(uuid.uuid4()), job_id, et, json.dumps({"text": prompt}), "pending"))
    else: raise HTTPException(status_code=400, detail="A prompt or a file is required. | Se requiere un prompt o un archivo.")
    conn.commit()
    conn.close()
    return {"status": "success", "job_id": job_id}

@app.get("/request-assignment/{worker_id}")
def request_assignment(worker_id: str):
    # --- English ---
    # Assigns an expert role to a worker based on current network demand.
    # --- Español ---
    # Asigna un rol de experto a un worker basándose en la demanda actual de la red.
    conn = get_db_connection()
    pending_counts = {expert: conn.execute("SELECT COUNT(*) FROM sub_tasks WHERE expert_type = ? AND status = 'pending'", (expert,)).fetchone()[0] for expert in SUPPORTED_EXPERTS}
    file_experts = ["document-summarization", "image-captioning", "audio-transcription"]
    for fe in file_experts:
        if pending_counts.get(fe, 0) > 0:
            assigned_expert = fe; break
    else:
         assigned_expert = max(pending_counts, key=pending_counts.get) if any(pending_counts.values()) else "text-generation"
    model_info = SUPPORTED_EXPERTS[assigned_expert]
    conn.execute("UPDATE workers SET assigned_expert = ?, status = 'idle' WHERE id = ?", (assigned_expert, worker_id))
    conn.commit()
    conn.close()
    return {"assigned_expert": assigned_expert, "model_info": model_info}

@app.get("/get-sub-task/{worker_id}/{expert_type}")
def get_sub_task(worker_id: str, expert_type: str):
    # --- English ---
    # Provides a pending sub-task to a requesting worker of the correct expert type.
    # --- Español ---
    # Entrega una subtarea pendiente a un worker que la solicita y es del tipo de experto correcto.
    conn = get_db_connection()
    sub_task = conn.execute("SELECT * FROM sub_tasks WHERE expert_type = ? AND status = 'pending' LIMIT 1", (expert_type,)).fetchone()
    if sub_task:
        conn.execute("UPDATE sub_tasks SET status = 'assigned', assigned_worker_id = ? WHERE id = ?", (worker_id, sub_task['id']))
        conn.execute("UPDATE workers SET status = 'busy' WHERE id = ?", (worker_id,))
        conn.commit()
        conn.close()
        return dict(sub_task)
    conn.close()
    return {"message": "No tasks available."}

@app.post("/submit-sub-task-result")
def submit_sub_task_result(payload: SubTaskResultPayload):
    # --- English ---
    # Receives the result of a sub-task and rewards the worker with reputation.
    # --- Español ---
    # Recibe el resultado de una subtarea y recompensa al worker con reputación.
    conn = get_db_connection()
    conn.execute("UPDATE sub_tasks SET status = 'completed', result = ? WHERE id = ?", (payload.result, payload.sub_task_id))
    conn.execute("UPDATE workers SET status = 'idle', reputation = reputation + 1.0 WHERE id = ?", (payload.worker_id,))
    sub_task = conn.execute("SELECT job_id FROM sub_tasks WHERE id = ?", (payload.sub_task_id,)).fetchone()
    if sub_task:
        job_id = sub_task['job_id']
        pending_count = conn.execute("SELECT COUNT(*) FROM sub_tasks WHERE job_id = ? AND status != 'completed'", (job_id,)).fetchone()[0]
        if pending_count == 0:
            all_results = conn.execute("SELECT expert_type, result FROM sub_tasks WHERE job_id = ?", (job_id,)).fetchall()
            final_result = {res['expert_type']: json.loads(res['result']) for res in all_results}
            conn.execute("UPDATE jobs SET status = 'completed', final_result = ? WHERE id = ?", (json.dumps(final_result, indent=2), job_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/get-job-status/{job_id}")
def get_job_status(job_id: str):
    # --- English ---
    # API endpoint for the web UI to poll for job results.
    # --- Español ---
    # Endpoint de la API para que la interfaz web consulte los resultados de un trabajo.
    conn = get_db_connection()
    job = conn.execute("SELECT status, final_result FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not job: raise HTTPException(status_code=404, detail="Job not found. | Trabajo no encontrado.")
    return dict(job)

@app.get("/", response_class=HTMLResponse)
def get_chat_ui():
    # --- English ---
    # Serves the complete web application (HTML, CSS, JavaScript).
    # --- Español ---
    # Sirve la aplicación web completa (HTML, CSS, JavaScript).
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat de IA Distribuida</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #f0f2f5; display: flex; flex-direction: column; height: 100vh; }
            #chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
            .message { max-width: 70%; margin-bottom: 15px; padding: 10px 15px; border-radius: 18px; line-height: 1.4; }
            .user { background: #0084ff; color: white; align-self: flex-end; margin-left: auto; }
            .assistant { background: #e4e6eb; color: #050505; align-self: flex-start; }
            .assistant pre { background: #d0d2d6; padding: 10px; border-radius: 8px; white-space: pre-wrap; word-wrap: break-word; }
            #input-area { display: flex; padding: 10px; background: #fff; border-top: 1px solid #ddd; align-items: center; }
            #prompt-input { flex: 1; border: 1px solid #ccc; border-radius: 18px; padding: 10px 15px; font-size: 16px; resize: none; }
            #send-button, #file-button { background: #0084ff; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; margin-left: 10px; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
            #file-input { display: none; }
        </style>
    </head>
    <body>
        <div id="chat-container"></div>
        <div id="input-area">
            <textarea id="prompt-input" placeholder="Escribe tu mensaje o sube un archivo..." rows="1"></textarea>
            <input type="file" id="file-input">
            <button id="file-button" title="Subir archivo">📎</button>
            <button id="send-button" title="Enviar">➤</button>
        </div>
        <script>
            const chatContainer = document.getElementById('chat-container');
            const promptInput = document.getElementById('prompt-input');
            const sendButton = document.getElementById('send-button');
            const fileButton = document.getElementById('file-button');
            const fileInput = document.getElementById('file-input');

            let workerId = new URLSearchParams(window.location.search).get('worker_id');
            if (!workerId) {
                addMessage("assistant", "<strong>Error:</strong> No se encontró un ID de worker. Por favor, inicia tu 'worker.py' y usa la URL que te proporciona en la consola para acceder a esta página.");
            } else {
                addMessage("assistant", "¡Conectado! Ya puedes chatear con la red de IA o subir un archivo.");
            }

            fileButton.addEventListener('click', () => fileInput.click());
            sendButton.addEventListener('click', sendMessage);
            promptInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });

            async function sendMessage() {
                const prompt = promptInput.value.trim();
                const file = fileInput.files[0];
                if (!prompt && !file) return;

                const userMessage = prompt || `Archivo subido: ${file.name}`;
                addMessage("user", userMessage);
                promptInput.value = ''; fileInput.value = '';

                const formData = new FormData();
                formData.append('worker_id', workerId);
                formData.append('prompt', prompt);
                if (file) formData.append('file', file);

                try {
                    const response = await fetch('/upload-and-submit-job', { method: 'POST', body: formData });
                    const data = await response.json();
                    if (!response.ok) throw new Error(data.detail || `HTTP error ${response.status}`);
                    
                    addMessage("assistant", "Procesando tu solicitud...", data.job_id);
                    pollJobStatus(data.job_id);
                } catch (error) {
                    addMessage("assistant", `<strong>Error al enviar el trabajo:</strong> ${error.message}`);
                }
            }
            
            function pollJobStatus(jobId) {
                const interval = setInterval(async () => {
                    try {
                        const response = await fetch(`/get-job-status/${jobId}`);
                        const data = await response.json();
                        if (data.status === 'completed') {
                            clearInterval(interval);
                            let resultText = "<strong>Tarea completada.</strong>";
                            if(data.final_result) {
                                const finalResult = JSON.parse(data.final_result);
                                resultText += Object.entries(finalResult).map(([key, value]) => `<hr><strong>Resultado de experto en '${key}':</strong><br><pre>${JSON.stringify(value, null, 2)}</pre>`).join('');
                            }
                            updateMessage(jobId, resultText);
                        }
                    } catch (error) {
                        clearInterval(interval);
                        updateMessage(jobId, `Error al obtener el estado del trabajo: ${error.message}`);
                    }
                }, 3000);
            }

            function addMessage(sender, text, id = null) {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message', sender);
                if (id) messageDiv.dataset.jobId = id;
                messageDiv.innerHTML = text;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            function updateMessage(jobId, newText) {
                const messageDiv = document.querySelector(`[data-job-id="${jobId}"]`);
                if (messageDiv) messageDiv.innerHTML = newText;
            }
        </script>
    </body>
    </html>
    """

