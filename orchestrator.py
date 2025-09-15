# --- English ---
# FINAL ORCHESTRATOR - READY FOR PUBLIC DEPLOYMENT
#
# This file is the central server. It should be run on a public server or VPS.
# It manages the entire network, serves the chat UI, and validates all interactions.
#
# HOW TO DEPLOY:
# 1. Upload this file to your public server.
# 2. Create a folder named 'uploads' in the same directory.
# 3. Run using a production-ready command:
#    uvicorn orchestrator:app --host 0.0.0.0 --port 8000
# 4. Make sure your server's firewall allows traffic on port 8000.

# --- Español ---
# ORQUESTADOR FINAL - LISTO PARA DESPLIEGUE PÚBLICO
#
# Este archivo es el servidor central. Debe ejecutarse en un servidor público o VPS.
# Gestiona toda la red, sirve la interfaz de chat y valida todas las interacciones.
#
# CÓMO DESPLEGAR:
# 1. Sube este archivo a tu servidor público.
# 2. Crea una carpeta llamada 'uploads' en el mismo directorio.
# 3. Ejecútalo usando un comando de producción:
#    uvicorn orchestrator:app --host 0.0.0.0 --port 8000
# 4. Asegúrate de que el firewall de tu servidor permite el tráfico en el puerto 8000.

# -*- coding: utf-8 -*-

import uuid
import json
import sqlite3
import time
import asyncio
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional
from fastapi.responses import HTMLResponse

# --- English ---
# --- Configuration ---
# --- Español ---
# --- Configuración ---
DB_FILE = "orchestrator_chat_prod.db"

# --- English ---
# This value is set to 0.0 for testing purposes.
# TODO: Increase this value in production for security.
# --- Español ---
# Este valor está en 0.0 para propósitos de prueba.
# TODO: Aumentar este valor en producción por seguridad.
REPUTATION_THRESHOLD_TO_SUBMIT = 0.0

HEARTBEAT_TIMEOUT_SECONDS = 120 # 2 minutes
UPLOAD_DIRECTORY = "uploads"

# --- English ---
# Using a single, powerful model for general AI tasks.
# --- Español ---
# Usando un único modelo potente para tareas de IA generales.
SUPPORTED_EXPERTS = {
    "general-ai": {"model": "google/gemma-2b-it", "task": "text-generation"},
    "document-summarization": {"model": "t5-small", "task": "summarization"},
    "image-captioning": {"model": "Salesforce/blip-image-captioning-large", "task": "image-to-text"},
    "audio-transcription": {"model": "openai/whisper-tiny.en", "task": "automatic-speech-recognition"}
}

# --- English ---
# --- Database Functions ---
# --- Español ---
# --- Funciones de la Base de Datos ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS workers (id TEXT PRIMARY KEY, assigned_expert TEXT, specs TEXT, status TEXT, reputation REAL, last_heartbeat INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, prompt TEXT, status TEXT, final_result TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sub_tasks (id TEXT PRIMARY KEY, job_id TEXT, expert_type TEXT, data TEXT, status TEXT, assigned_worker_id TEXT, result TEXT, FOREIGN KEY (job_id) REFERENCES jobs (id))''')
    conn.commit()
    conn.close()

# --- English ---
# --- Background Task for Purging Inactive Workers ---
# --- Español ---
# --- Tarea en Segundo Plano para Purgar Workers Inactivos ---
async def purge_inactive_workers():
    while True:
        await asyncio.sleep(60)
        timeout_threshold = int(time.time()) - HEARTBEAT_TIMEOUT_SECONDS
        conn = get_db_connection()
        inactive_ids_tuples = conn.execute("SELECT id FROM workers WHERE last_heartbeat < ?", (timeout_threshold,)).fetchall()
        if inactive_ids_tuples:
            inactive_ids = [row['id'] for row in inactive_ids_tuples]
            placeholders = ', '.join('?' for _ in inactive_ids)
            conn.execute(f"DELETE FROM workers WHERE id IN ({placeholders})", inactive_ids)
            conn.commit()
            print(f"👻 Purged {len(inactive_ids)} inactive worker(s). | Purgados {len(inactive_ids)} worker(s) inactivos.")
        conn.close()

app = FastAPI(title="Distributed AI Orchestrator | Orquestador de IA Distribuida", version="12.0.0")

@app.on_event("startup")
async def on_startup():
    init_db()
    asyncio.create_task(purge_inactive_workers())

# --- English ---
# --- Pydantic Models for Data Validation ---
# --- Español ---
# --- Modelos Pydantic para Validación de Datos ---
class WorkerSpecs(BaseModel): gpu: str; cpu_cores: int; memory: str
class WorkerRegistrationPayload(BaseModel): specs: WorkerSpecs
class HeartbeatPayload(BaseModel): worker_id: str
class SubTaskResultPayload(BaseModel): worker_id: str; sub_task_id: str; result: str

# --- English ---
# --- API Endpoints for Workers ---
# --- Español ---
# --- Endpoints de la API para los Workers ---
@app.post("/register")
def register_worker(payload: WorkerRegistrationPayload):
    worker_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute("INSERT INTO workers (id, specs, status, reputation, last_heartbeat) VALUES (?, ?, ?, ?, ?)",
                 (worker_id, json.dumps(payload.specs.dict()), "pending_assignment", 0.0, int(time.time())))
    conn.commit()
    conn.close()
    return {"status": "success", "worker_id": worker_id}

@app.post("/heartbeat")
def heartbeat(payload: HeartbeatPayload):
    conn = get_db_connection()
    result = conn.execute("UPDATE workers SET last_heartbeat = ? WHERE id = ?", (int(time.time()), payload.worker_id))
    conn.commit()
    conn.close()
    if result.rowcount == 0: raise HTTPException(status_code=404, detail="Worker not found or purged. Please restart.")
    return {"status": "acknowledged"}

@app.get("/request-assignment/{worker_id}")
def request_assignment(worker_id: str):
    conn = get_db_connection()
    pending_counts = {expert: conn.execute("SELECT COUNT(*) FROM sub_tasks WHERE expert_type = ? AND status = 'pending'", (expert,)).fetchone()[0] for expert in SUPPORTED_EXPERTS}
    file_experts = ["document-summarization", "image-captioning", "audio-transcription"]
    
    assigned_expert = "general-ai" # Asignar 'general-ai' por defecto

    # --- English ---
    # Check if there are urgent file-processing tasks. If so, re-assign.
    # --- Español ---
    # Comprobar si hay tareas urgentes de procesamiento de archivos. Si es así, reasignar.
    for fe in file_experts:
        if pending_counts.get(fe, 0) > 0:
            assigned_expert = fe
            break
    
    model_info = SUPPORTED_EXPERTS[assigned_expert]
    conn.execute("UPDATE workers SET assigned_expert = ?, status = 'idle' WHERE id = ?", (assigned_expert, worker_id))
    conn.commit()
    conn.close()
    return {"assigned_expert": assigned_expert, "model_info": model_info}

@app.get("/get-sub-task/{worker_id}/{expert_type}")
def get_sub_task(worker_id: str, expert_type: str):
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

# --- English ---
# --- API Endpoints for Web UI ---
# --- Español ---
# --- Endpoints de la API para la Interfaz Web ---
@app.post("/upload-and-submit-job")
async def upload_and_submit_job(worker_id: str = Form(...), prompt: str = Form(""), file: Optional[UploadFile] = File(None)):
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
        # --- English Prompt Template for the Gemma model ---
        prompt_template = f"<start_of_turn>user\nAnalyze the following text and provide two responses in a single JSON code block: 1. 'summary': a concise one-sentence summary. 2. 'generation': a creative continuation or a relevant response to the text.\n\nUser text: \"{prompt}\"\n\nYour JSON response:<end_of_turn>\n<start_of_turn>model\n"
        conn.execute("INSERT INTO sub_tasks (id, job_id, expert_type, data, status) VALUES (?, ?, ?, ?, ?)",
                     (str(uuid.uuid4()), job_id, "general-ai", json.dumps({"text": prompt_template}), "pending"))
    else: raise HTTPException(status_code=400, detail="A prompt or a file is required. | Se requiere un prompt o un archivo.")
    conn.commit()
    conn.close()
    return {"status": "success", "job_id": job_id}

@app.get("/get-job-status/{job_id}")
def get_job_status(job_id: str):
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