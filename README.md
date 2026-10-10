# 💬 Offline ChatGPT Clone (LocalMind Evolution)

A complete **ChatGPT-like offline AI assistant** powered by **Ollama** and a clean, pure Python interface.

This project runs **fully offline** using local LLMs — no external cloud API or internet connection required after setup.

---

## 🔄 Project Evolution: LocalMind (Streamlit Upgrade)

We are upgrading this project in-place to **LocalMind**, transitioning from the initial HTML/CSS/JS frontend to a pure-Python **Streamlit** architecture:
- **Zero Frontend Hassle**: Pure Python UI with native streaming (`st.write_stream`) and responsive components.
- **Hardware-Aware Model Recommendations**: Probes your RAM, CPU, and GPU to categorize hardware into tiers (Light/Medium/Strong) and recommend compatible models with traffic-light verdicts (Green/Yellow/Red).
- **Safe Offline Slash Commands**: Execute administrative actions (`/models`, `/running`, `/unload`, `/system`, `/clear`, `/help`) directly in chat without invoking the LLM.
- **Persistent SQLite Storage**: Preserves conversation history, searchable logs, and exports to Markdown and JSON.
- **Performance & Eco Controls**: Customizable personas, generation parameters, Eco Mode, and real-time resource gauges.
- **Optional Cloud Fallback**: Support for user-provided OpenAI-compatible keys with clear privacy disclaimers and quota alerts.
- **Legacy Preservation**: The original FastAPI (`backend/`) and web client (`frontend/`) code is retained and will be safely archived to `legacy/` once Phase 1 is validated.

---

# 🚀 Features

- 🌐 Modern Streamlit & ChatGPT-style UI
- 🧠 Fully Offline AI using Ollama
- ⚡ Fast local response generation & live streaming
- 🗂️ Chat history sidebar with SQLite persistence
- ➕ New Chat & Clear Chat support
- 🤖 Multiple model selection & hardware tier recommendations
- 📎 File upload button (in-context PDF/TXT reading)
- 🎤 Microphone button (offline Whisper transcription)
- 🔄 Real-time chat rendering via `st.write_stream`
- 📱 Responsive design
- 🔌 Backend-ready architecture with clean separation in `core/`
- 📳 Models used: `qwen2.5-coder`, `mistral`, `gemma`, `phi3`, `llama3`

---

# 📁 Target Project Structure

```bash
offline_Ai_chatbot/
├── app.py                 # Streamlit entry point
├── pages/                 # Multi-page UI (Chat, Hardware & Models, Settings)
├── core/                  # Pure Python logic (Ollama client, system info, recommender, db)
├── tests/                 # Automated test suite (pytest)
├── docs/                  # Architecture, plan, database schema, commands, progress
│   ├── PLAN.md
│   ├── AUDIT.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── COMMANDS.md
│   ├── PROGRESS.md
│   └── phases/
├── legacy/                # Archived original backend/ and frontend/ (post-Phase 1)
├── backend/               # Current FastAPI backend (preserved during migration)
├── frontend/              # Current HTML/JS frontend (preserved during migration)
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

# 🧠 Tech Stack

## Frontend (Upgraded)
- Streamlit (Pure Python UI)

## Legacy Frontend (Preserved)
- HTML5, CSS3, JavaScript

## Core Logic & Backend
- Python 3.12+ (FastAPI / HTTPX client / SQLite / psutil)

## AI Runtime
- Ollama (Local LLM Daemon)

---

# 🛠️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/Anuj04432/Offline_AI_Assistant.git
cd Offline_AI_Assistant
```

---

# 📥 Install Ollama

Download and install Ollama from:

👉 https://ollama.com

Verify installation:

```bash
ollama --version
```

---

# 🤖 Download a Model

Example:

```bash
ollama pull qwen2.5-coder:7b
# or lighter models:
ollama pull qwen2.5:1.5b
ollama pull mistral:7b
```

---

# ⚙️ Environment Setup

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Application

### Option A: Running LocalMind (Streamlit - Recommended)
```bash
streamlit run app.py
```

### Option B: Running Legacy FastAPI Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
Open `frontend/index.html` in your browser.

---

# 🛡️ Privacy

This project is completely offline.

- No cloud API required
- No data collection or tracking
- No internet dependency for local models
- Full local execution

Your chats never leave your device.

---

# 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss improvements.

---

# 📜 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

### Anuj Wagmore
GitHub: https://github.com/Anuj04432