# Phase 6: Document Attachment, Offline Voice, Tests, CI & Docker

## 1. Goal
Complete the production readiness of LocalMind by adding offline multimodal enhancements (document text attachment and offline speech-to-text), automated unit and integration tests, continuous integration (CI) workflows, Docker containerization, and comprehensive project documentation suitable for interview demonstrations.

---

## 2. Existing Code Reused in Phase 6
- **`backend/main.py` (`POST /upload`)**: Reuses the PDF and TXT text extraction logic (using `PyPDF2.PdfReader` / `pypdf`), refactoring it into a clean helper module in `core/file_reader.py`.
- **`backend/main.py` (`POST /voice`)**: Replaces the static voice stub endpoint with a real local speech-to-text pipeline in `core/audio.py` powered by `faster-whisper`.

---

## 3. Tasks Checklist
- [ ] Implement Document Text Ingestion in `core/file_reader.py`:
  - [ ] Extract raw text from uploaded `.txt` files (reused from `backend/main.py`)
  - [ ] Extract page text from uploaded `.pdf` files using `PyPDF2` (reused from `backend/main.py`)
  - [ ] Sanitize extracted text and format as context block inside the chat prompt
- [ ] Implement Offline Voice Transcription in `core/audio.py`:
  - [ ] Integrate local `faster-whisper` using lightweight model (e.g. `base.en` or `tiny.en`)
  - [ ] Transcribe user audio recordings completely offline on CPU/GPU
  - [ ] Integrate Streamlit audio recorder widget in `pages/1_Chat.py`
- [ ] Automated Test Suite in `tests/`:
  - [ ] `test_ollama_client.py`: Mocked HTTP streaming, status checks, error handling
  - [ ] `test_system_info.py`: RAM, CPU, GPU detection under mocked environments
  - [ ] `test_recommender.py`: Hardware tier categorization and traffic-light verdicts
  - [ ] `test_command_router.py`: Slash command interception, argument extraction, error conditions
  - [ ] `test_subprocess_runner.py`: Whitelist rejection, regex validation, timeout handling
  - [ ] `test_db.py`: SQLite initialization, migrations, CRUD, cascade deletion, search
  - [ ] `test_providers.py`: Provider switching, token tallying, quota enforcement
- [ ] Continuous Integration (CI):
  - [ ] Create `.github/workflows/ci.yml` running linting (`ruff`), type checking, and `pytest`
- [ ] Containerization:
  - [ ] Create `Dockerfile` (Python 3.12, non-root user, Streamlit config)
  - [ ] Create `docker-compose.yml` linking Streamlit app to local host network for Ollama access
- [ ] Final Documentation & Demonstration Assets:
  - [ ] Update root `README.md` with architecture diagram, installation steps, and features
  - [ ] Prepare an interview demo script walking through offline capabilities

---

## 3. Files to Create / Edit
- `core/file_reader.py` — Text and PDF document parsing (refactored from backend/main.py)
- `core/audio.py` — Offline speech-to-text with `faster-whisper`
- `pages/1_Chat.py` — File uploader and audio input UI integration
- `tests/*` — Complete suite of unit and integration tests
- `.github/workflows/ci.yml` — Automated GitHub Actions CI workflow
- `Dockerfile` & `docker-compose.yml` — Production container definitions
- `README.md` — Polished project documentation

---

## 4. Acceptance Criteria
1. Users can attach a `.txt` or `.pdf` file in chat; the system extracts the text and prepends it to the prompt as context without calling any cloud service.
2. Users can record voice audio directly in the browser; the audio is transcribed offline by `faster-whisper` and inserted into the chat input.
3. All unit tests pass with `pytest` with zero warnings or errors.
4. CI pipeline passes automated linting and test runs.
5. The application builds and runs reliably inside Docker.
6. The `README.md` provides clear, copy-pasteable instructions for running LocalMind on any machine.

---

## 5. How to Test Manually
1. **Document Attachment Test**:
   - Attach a sample PDF document (e.g., a 2-page project summary).
   - Enter prompt: `"Summarize the key points in this attached document."`
   - Confirm the local LLM generates an accurate summary based on the extracted text.
2. **Offline Speech-to-Text Test**:
   - Record a 5-second audio snippet speaking: `"What is the capital of France?"`
   - Confirm offline transcription runs locally and submits the prompt to the chat.
3. **Automated Test Run**:
   - Execute `pytest -v` from the project root.
   - Confirm 100% test pass rate across all test modules.
4. **Docker Build & Run Test**:
   - Run `docker compose up --build`.
   - Access `http://localhost:8501` and verify full app functionality.

---

## 6. Interview Talking Points
- **RAG vs. Direct In-Context Ingestion**: Explaining the architectural trade-off: for small documents (< 10 pages), direct in-context injection avoids the complexity and overhead of vector databases, chunking algorithms, and embedding generation while preserving full semantic coherence.
- **Offline Multimodal Engineering**: How running Whisper locally using optimized runtimes like `faster-whisper` (CTranslate2) enables sub-second voice transcription on standard CPUs without GPU acceleration or cloud latency.
- **Production Hardening in Python**: Explaining how automated CI testing, type hints, containerization, and reproducible environments transform an experimental project into an enterprise-grade portfolio piece.
