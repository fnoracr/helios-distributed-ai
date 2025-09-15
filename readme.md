Helios Distributed AI Network
An open-source platform for building a decentralized AI computing network. Users contribute idle resources via a multi-modal worker, forming a global supercomputer for complex AI tasks (text, image, audio) managed by an orchestrator server.

Red de IA Distribuida Helios
Una plataforma de código abierto para construir una red de computación de IA descentralizada. Los usuarios contribuyen con sus recursos inactivos a través de un worker multi-modal, formando una supercomputadora global para tareas de IA complejas (texto, imagen, audio) gestionada por un servidor orquestador.

🇬🇧 English
Key Features
🌐 Decentralized Network: Leverages idle computing power from user devices around the world to create a powerful, distributed AI supercomputer.

🧠 Multi-Modal AI: Capable of processing not just text, but also documents (.pdf, .docx), images (.png, .jpg), and audio (.mp3, .wav).

🛡️ Proof-of-Contribution: A secure and fair system. To use the network's AI capabilities, a user must first contribute by running a worker node. Access is granted automatically based on active and reputable contributions.

🤖 Dynamic Experts: Worker nodes are dynamically assigned AI models based on the network's current demand, ensuring efficient resource allocation.

💻 Cross-Platform: Easy-to-use installers for both Windows and Linux, allowing anyone to join the network with just a few clicks.

How It Works: Architectural Overview
The Helios network consists of two main components:

The Orchestrator (orchestrator.py): The central server and brain of the network. It runs on a public server and manages worker registration, job distribution, and the web chat UI.

The Worker (worker.py): The client application that users run on their machines. It connects to the Orchestrator, receives AI model assignments, processes tasks, and sends heartbeats to prove its activity.

Getting Started (For Users)
To join the Helios network, simply install the worker client for your operating system.

Windows: Download and run the HeliosAIWorker\_Setup.exe from the Releases page. The installer will automatically configure the worker to run on startup and place a "Helios AI Chat" shortcut on your desktop.

Linux: Download the latest helios-ai-worker-linux-vX.X.tar.gz from the Releases page. Extract it and run sudo bash install.sh. An application launcher will be added to your desktop environment.

After installation, click the "Helios AI Chat" shortcut to open your personal, authenticated chat session in your web browser.
Uninstall Instructions
To completely remove the Helios AI Worker from your system, navigate to the extracted folder and run the uninstall script with sudo:

Bash

sudo ./uninstall.sh
License \& Commercial Use
This project is open-source and free for personal, non-commercial use only. All users are free to view, modify, and extend the source code for personal purposes.

Any individual or entity wishing to use all or part of this code in commercial projects must notify Noragentia and may not do so without express written permission. The use of this software or any modified version of it for commercial, business, or enterprise purposes is strictly prohibited without a formal commercial agreement.

To inquire about a commercial license, please contact:

Noragentia

Website: https://www.noragentia.com

Email: info@noragentia.com

Please see the license.txt file for the full terms.

🇪🇸 Español
Características Clave
🌐 Red Descentralizada: Aprovecha la potencia de cálculo inactiva de los dispositivos de los usuarios para crear una potente supercomputadora de IA distribuida.

🧠 IA Multi-Modal: Capaz de procesar texto, documentos (.pdf, .docx), imágenes (.png, .jpg) y audio (.mp3, .wav).

🛡️ Prueba de Contribución: Un sistema seguro y justo. Para usar la red, un usuario primero debe contribuir ejecutando un nodo worker. El acceso se concede automáticamente basándose en contribuciones activas y con buena reputación.

🤖 Expertos Dinámicos: A los nodos worker se les asignan modelos de IA de forma dinámica según la demanda de la red, asegurando una asignación eficiente de recursos.

💻 Multiplataforma: Instaladores fáciles de usar para Windows y Linux, permitiendo que cualquiera se una a la red con solo unos clics.

Cómo Funciona: Resumen de la Arquitectura
La red Helios consta de dos componentes principales:

El Orquestador (orchestrator.py): El servidor central y cerebro de la red. Se ejecuta en un servidor público y gestiona el registro de workers, la distribución de trabajos y la interfaz de chat web.

El Worker (worker.py): La aplicación cliente que los usuarios ejecutan en sus ordenadores. Se conecta al Orquestador, recibe asignaciones de modelos de IA, procesa tareas y envía heartbeats para demostrar su actividad.

Cómo Empezar (Para Usuarios)
Para unirte a la red Helios, solo necesitas instalar el cliente worker para tu sistema operativo.

Windows: Descarga y ejecuta el HeliosAIWorker\_Setup.exe desde la página de Releases. El instalador configurará automáticamente el worker para que se ejecute al arrancar y creará un acceso directo "Helios AI Chat" en tu escritorio.

Linux: Descarga el último helios-ai-worker-linux-vX.X.tar.gz desde la página de Releases. Extráelo y ejecuta sudo bash install.sh. Se añadirá un lanzador de aplicación a tu entorno de escritorio.

Instrucciones de Desinstalación

Para eliminar completamente el Helios AI Worker de tu sistema, navega a la carpeta descomprimida y ejecuta el script de desinstalación con `sudo`:

```bash
sudo ./uninstall.sh
```
Después de la instalación, haz clic en el acceso directo "Helios AI Chat", que abrirá tu sesión de chat personal y autenticada en tu navegador web.

Licencia y Uso Comercial
Este proyecto es de código abierto y gratuito para uso personal y no comercial exclusivamente. Todos los usuarios son libres de ver, modificar y ampliar el código fuente para fines personales.

Cualquier individuo o entidad que desee utilizar todo o parte de este código en proyectos comerciales deberá comunicárselo a Noragentia y no podrá hacerlo sin permiso expreso por escrito. El uso de este software o de cualquier versión modificada del mismo con fines comerciales, de negocio o empresariales está estrictamente prohibido sin un acuerdo comercial formal.

Para solicitar una licencia de uso comercial contacte por favor con:
Noragentia

Website: https://www.noragentia.com

Email: info@noragentia.com

Por favor, lea license.txt para conocer todos los términos y condiciones de uso.

