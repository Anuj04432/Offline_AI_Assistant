# LocalMind — In-Place Project Migration Plan

## 1. Project Goal & Migration Context
This project is an in-place migration and upgrade of the existing **`offline_Ai_chatbot`** codebase into **LocalMind** — an offline, private AI assistant built strictly with **Streamlit** (pure Python, zero custom HTML/CSS/JS).

The existing project contains:
- `backend/main.py`: FastAPI backend proxying requests to local Ollama, managing in-memory sessions, handling `/models`, `/chat`, and PDF `/upload`.
- `frontend/`: HTML5, CSS3, and JavaScript web client with a terminal-inspired theme.
- `pyproject.toml` & `requirements.txt`: Python package configuration.

### Why Migrate?
- **Zero Frontend Overhead**: Replacing custom HTML/CSS/JS with Streamlit simplifies UI maintenance and eliminates boilerplate bridge code.
- **Native Token Streaming**: Upgrades blocking responses to real-time token streaming (`st.write_stream`).
- **Hardware Awareness**: Introduces device inspection (`psutil`) and intelligent model tier recommendations (Light/Medium/Strong).
- **Safe Offline Administration**: Adds whitelisted, regex-validated slash commands (`/models`, `/running`, `/unload`, etc.) running before LLM execution.
- **Relational Persistence**: Replaces fragile in-memory dictionaries with an embedded SQLite database (`localmind.db`).
- **Code Preservation**: Existing `backend/` and `frontend/` folders are kept intact during development and will be moved to `legacy/` only after Phase 1 is approved.

---

## 2. Technology Stack & Environment

| Component | Target Technology | Rationale / Migration Source |
| :--- | :--- | :--- |
| **Language** | Python 3.12 (Recommended) | Stable binary wheels for ML/audio (downgrading from experimental `>=3.14`) |
| **UI Framework** | Streamlit | Pure Python UI replacing `frontend/index.html`, `script.js`, `style.css` |
| **Local LLM Engine** | Ollama (`:11434`) | Reused from current `OLLAMA_BASE_URL` setup in `backend/main.py` |
| **HTTP Client** | `httpx` | Upgraded to streaming generator pattern for token-by-token output |
| **Hardware Probing**| `psutil`, `shutil` | System RAM, CPU cores, GPU detection |
| **Database** | SQLite (`sqlite3`) | Embedded persistent storage replacing `backend/main.py` `sessions` dict |
| **File Extraction** | `PyPDF2` / `pypdf` | Reused directly from `backend/main.py` `/upload` endpoint |
| **Testing** | `pytest`, `pytest-mock` | Automated testing for all `core/` business logic modules |

---

## 3. Target Folder Structure

```bash
offline_Ai_chatbot/
├── app.py                 # Streamlit entry point
├── pages/                 # Multi-page UI (Chat, Hardware & Models, Settings)
├── core/                  # Pure Python logic (ollama_client, system_info, recommender, db)
├── tests/                 # Automated test suite (pytest)
├── docs/                  # Architecture, plan, audit, database schema, commands, progress
│   ├── PLAN.md
│   ├── AUDIT.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── COMMANDS.md
│   ├── PROGRESS.md
│   └── phases/
├── legacy/                # Archived old backend/ and frontend/ (moved AFTER Phase 1 works)
├── backend/               # Current FastAPI backend (preserved during Phase 1)
├── frontend/              # Current HTML/JS frontend (preserved during Phase 1)
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 4. Preservation & Migration Rules for Legacy Code

1. **Do Not Delete**: Neither `backend/` nor `frontend/` will be deleted during this migration.
2. **Move to Legacy Post-Phase 1**: Only after Phase 1 is verified, working, and explicitly approved by the user, `backend/` and `frontend/` will be moved into `legacy/`.
3. **Reuse Existing Logic**:
   - `backend/main.py` Ollama discovery -> `core/ollama_client.py`
   - `backend/main.py` Chat invocation -> `core/ollama_client.py`
   - `backend/main.py` PDF text extraction -> `core/file_reader.py`
   - `frontend/script.js` Model badge categories -> `core/recommender.py`
4. **Thin UI Enforcement**: No business logic or subprocess calls in `pages/`; all logic lives in `core/`.

---

## 5. Explicitly Out-of-Scope (Deferred)

- **RAG & Vector DBs**: No ChromaDB, FAISS, or chunking pipelines for now.
- **Model Fine-Tuning**: No LoRA or dataset training.
- **Custom HTML/CSS/JS**: UI is 100% native Streamlit components.
- **Cloud Accounts**: Single-user local application only.
