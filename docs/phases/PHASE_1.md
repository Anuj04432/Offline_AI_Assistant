# Phase 1: Working Local Chat (MVP)

## 1. Goal
Build the core, functional Minimum Viable Product (MVP) of LocalMind inside the existing project root.
Users can open the Streamlit web application, verify that Ollama is installed and running, select an installed local model from a dropdown, and engage in real-time, token-streaming conversations that maintain conversational context within session state.

---

## 2. Existing Code Reused in Phase 1
- **`backend/main.py` (`GET /models`)**: Reuses the logic querying Ollama's `GET /api/tags` to populate available local models.
- **`backend/main.py` (`POST /chat`)**: Reuses the chat payload structure (`messages`, `model`, system prompt). Upgrades the execution from blocking non-streaming (`stream: False`) to real-time token streaming (`stream: True`) using `httpx.stream`.
- **`backend/main.py` (Default Model)**: Reuses `DEFAULT_MODEL = "qwen2.5-coder:7b"` configuration fallback.

---

## 3. Tasks Checklist
- [ ] Implement `core/ollama_client.py`:
  - [ ] System check: check if `ollama` executable is present in PATH via `shutil.which`
  - [ ] Version check: query version via `GET /api/version` or safe subprocess `ollama --version`
  - [ ] Model list: fetch available models from `GET /api/tags` (reused from `backend/main.py`)
  - [ ] Chat stream: stream response tokens from `POST /api/chat` using `httpx.stream`
- [ ] Build `app.py` & `pages/1_Chat.py`:
  - [ ] Sidebar containing connection status pill (Green/Red) and model dropdown
  - [ ] Fallback warning with step-by-step troubleshooting when Ollama is unreachable
  - [ ] Message history rendering using `st.chat_message`
  - [ ] User input handling via `st.chat_input`
  - [ ] Response streaming using `st.write_stream`
  - [ ] "New Chat" and "Clear Chat" action buttons in the sidebar
- [ ] Maintain in-memory conversation history in `st.session_state["messages"]`
- [ ] Type hints and docstrings on every function in `core/ollama_client.py`
- [ ] Milestone review: Obtain user approval to archive `backend/` and `frontend/` to `legacy/`

---

## 4. Files to Create / Edit
- `core/config.py` — Default endpoints (`http://localhost:11434`), default model, timeout limits
- `core/ollama_client.py` — Ollama communication client with synchronous/streaming generators
- `app.py` — Streamlit entry point redirecting to the chat page or hosting primary layout
- `pages/1_Chat.py` — Streamlit chat UI page

---

## 5. Acceptance Criteria
1. If Ollama is running and has at least one model, the app displays a green "Ollama: Connected" status and lists installed models in the dropdown.
2. If Ollama is stopped, the app displays a clear warning: `"Could not connect to Ollama. Ensure Ollama is running ('ollama serve')."` without crashing with an unhandled exception.
3. Sending a message renders the user's prompt immediately in a chat bubble, followed by the assistant's reply streaming token-by-token.
4. Subsequent messages in the same session retain conversational context (the LLM remembers previous turns).
5. Clicking "New Chat" resets `st.session_state["messages"]` and clears the chat screen.
6. Zero custom HTML, CSS, or JavaScript code is used in the UI.
7. Existing `backend/` and `frontend/` directories remain completely intact.

---

## 6. How to Test Manually
1. **Ollama Offline Test**:
   - Terminate the Ollama service (`ollama stop` or kill the process).
   - Run `streamlit run app.py`.
   - Verify that the app shows the red disconnected banner and does not crash.
2. **Ollama Online & Model Discovery Test**:
   - Start Ollama (`ollama serve`).
   - Refresh the Streamlit page.
   - Verify that the status turns green and installed models appear in the select box.
3. **Streaming & Context Test**:
   - Send prompt: `"My name is Alice and my favorite color is teal."`
   - Observe smooth token streaming.
   - Send prompt: `"What is my favorite color and what is my name?"`
   - Verify that the model accurately recalls both facts from prior turns.
4. **Reset Test**:
   - Click "New Chat" in the sidebar.
   - Verify that the message history disappears and the context is cleared.

---

## 7. Interview Talking Points
- **Streamlit Execution Model**: Understanding how Streamlit re-executes the entire script from top to bottom on each interaction and why `st.session_state` is essential to preserve state across reruns.
- **Token Streaming via Generators**: Explaining how Python generators (`yield`) stream chunks over HTTP via `httpx.stream("POST", ...)`, seamlessly coupling with Streamlit's `st.write_stream` without blocking the main event loop.
- **Refactoring from REST Proxy to Direct Client**: Explaining why a local desktop app benefits from eliminating the intermediate FastAPI bridge layer in favor of direct async/sync client calls from Streamlit to Ollama.
