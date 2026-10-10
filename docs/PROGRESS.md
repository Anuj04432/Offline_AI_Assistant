# LocalMind — Project Progress & Migration Checklist

Legend:
- `[ ]` Not Started
- `[/]` In Progress
- `[x]` Completed

---

## Phase 0: Planning & Architectural Foundations (Migration Mode)
- [x] Consolidate project documentation in `./docs/`
- [x] Author `docs/AUDIT.md` (Codebase audit, reusable components, technical debt)
- [x] Author `docs/PLAN.md` (Migration plan, scope, Streamlit architecture, boundaries)
- [x] Author `docs/ARCHITECTURE.md` (Module responsibilities, data flow, legacy transition)
- [x] Author `docs/DATABASE.md` (SQLite schema, pragmas, indices, migrations)
- [x] Author `docs/COMMANDS.md` (Slash commands, whitelist, subprocess safety)
- [x] Author `docs/PROGRESS.md` (Master task checklist)
- [x] Author all phase specifications (`docs/phases/PHASE_1.md` through `PHASE_6.md`)
- [x] Merge `.gitignore`, `requirements.txt`, and root `README.md`
- [ ] Review plan and audit with user; obtain Phase 1 approval

---

## Phase 1: Working Local Chat (MVP)
- [ ] Check Ollama binary installation via `shutil.which` and version validation
- [ ] Implement `core/ollama_client.py`:
  - [ ] Refactor model listing from `backend/main.py` (`/models` -> `GET /api/tags`)
  - [ ] Refactor chat from `backend/main.py` (`/chat` -> streaming `POST /api/chat`)
- [ ] Build thin Streamlit UI in `app.py` & `pages/1_Chat.py`
- [ ] Integrate streaming token rendering via `st.write_stream`
- [ ] Implement in-memory conversation state via `st.session_state`
- [ ] Add "New Chat" and "Clear Chat" reset buttons
- [ ] Handle connection failure gracefully with troubleshooting instructions
- [ ] Manual test: End-to-end chat verification with local model
- [ ] User approval milestone: Archive `backend/` and `frontend/` to `legacy/`

---

## Phase 2: Device Check, Model Recommender, Onboarding & Slash Commands
- [ ] Implement `core/system_info.py` using `psutil` (RAM, CPU cores, GPU check)
- [ ] Implement `core/recommender.py`:
  - [ ] Port `frontend/script.js` model badging heuristic into Python
  - [ ] Light/Medium/Strong tiers + Green/Yellow/Red verdicts
- [ ] Create `pages/2_Hardware_&_Models.py` with system cards and guided onboarding
- [ ] Implement model pull flow with streaming progress indicators
- [ ] Implement `core/subprocess_runner.py` with strict whitelist, timeouts, and model regex validation
- [ ] Implement `core/command_router.py` for `/models`, `/running`, `/unload`, `/system`, `/clear`, `/help`
- [ ] Connect slash command interception in chat input before LLM execution
- [ ] Manual test: Verify slash commands, hardware probing, and model pull

---

## Phase 3: SQLite Persistent Chats, Search & Export
- [ ] Implement `core/db.py` with WAL mode and schema initialization (replacing `backend/main.py` `sessions` dict)
- [ ] Persist conversation metadata (`conversations` table) and turns (`messages` table)
- [ ] Build Streamlit sidebar conversation list with active selection
- [ ] Implement conversation renaming and deletion
- [ ] Implement conversation keyword search in sidebar
- [ ] Implement conversation export to Markdown (`.md`) and JSON format
- [ ] Manual test: Create multiple chats, restart Streamlit app, verify persistence

---

## Phase 4: Settings, Personas, Eco Mode & Hardware Monitor
- [ ] Implement persistent key-value configuration in `settings` table
- [ ] Create `pages/3_Settings.py` for generation parameters (temperature, top_p, max_tokens)
- [ ] Implement system prompt personas (Assistant, Senior Coder, Science Tutor, Creative Writer)
- [ ] Implement "Eco Mode" (token limits, lower generation footprint, lighter defaults)
- [ ] Add live RAM/CPU monitor widget in sidebar
- [ ] Implement context trimming logic (sliding window) to prevent context overflows
- [ ] Manual test: Verify persona switching, Eco Mode throttling, and settings persistence

---

## Phase 5: Optional Cloud API Fallback + Quota & Privacy Warning
- [ ] Design provider abstraction in `core/providers.py` (`OllamaProvider` & `OpenAIProvider`)
- [ ] Allow user to securely input and persist their own cloud API key (masked in UI, stored locally)
- [ ] Implement local usage counter (`usage_stats` table) tracking prompt and completion tokens
- [ ] Add "Quota reached, add your own key" flow when quota limits are met
- [ ] Implement mandatory privacy warning banner when switching to Cloud API mode
- [ ] Manual test: Test switching between Ollama and Cloud mode, verify warning and quota

---

## Phase 6: Document Attachment, Offline Voice, Tests, CI & Docker
- [ ] Implement `core/file_reader.py`:
  - [ ] Reuse `PyPDF2` text extraction logic from `backend/main.py`
  - [ ] Extract plain text from `.txt` files
- [ ] Allow attaching documents directly in chat to be injected as prompt context
- [ ] Implement `core/audio.py` for offline speech-to-text using local `faster-whisper`
- [ ] Add microphone recording widget in Streamlit interface
- [ ] Write unit tests for all core modules (`pytest` + `pytest-mock`)
- [ ] Add GitHub Actions CI workflow for linting (`ruff`) and testing (`pytest`)
- [ ] Create multi-stage `Dockerfile` and `docker-compose.yml`
- [ ] Complete comprehensive project `README.md`
