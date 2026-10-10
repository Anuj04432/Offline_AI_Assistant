# Phase 2: Device Check, Model Recommender, Onboarding & Slash Commands

## 1. Goal
Empower users to understand their hardware capabilities, receive intelligent model recommendations tailored to their system's RAM and GPU, download compatible models directly through the UI with live progress indicators, and execute safe offline slash commands directly from the chat input.

---

## 2. Existing Code Reused in Phase 2
- **`frontend/script.js` (`badgeForModel`)**: Reuses and ports the client-side model tagging heuristic (e.g. `coder` -> `Code`, `qwen`/`mistral` -> `Fast`, `llama` -> `Smart`, `phi` -> `Light`) into Python within `core/recommender.py` to drive hardware compatibility scoring.

---

## 3. Tasks Checklist
- [ ] Implement `core/system_info.py`:
  - [ ] Measure total, available, and percentage RAM using `psutil.virtual_memory()`
  - [ ] Count physical and logical CPU cores via `psutil.cpu_count()`
  - [ ] Query CPU utilization percentage via `psutil.cpu_percent()`
  - [ ] Detect GPU presence and VRAM (via `torch.cuda`, NVIDIA management, or platform detection) with graceful fallback
- [ ] Implement `core/recommender.py`:
  - [ ] Map host RAM/VRAM into tiers: Light (< 8 GB), Medium (8–16 GB), Strong (> 16 GB)
  - [ ] Provide model catalog recommendations based on tier (e.g. `qwen2.5:1.5b`, `llama3.2:3b`, `mistral:7b`, `llama3.1:8b`)
  - [ ] Compute green/yellow/red verdicts for installed and prospective models
- [ ] Implement `core/subprocess_runner.py`:
  - [ ] Whitelist permitted Ollama commands: `list`, `ps`, `show`, `stop`, `rm`, `--version`
  - [ ] Enforce strict regex validation for model names (`^[a-zA-Z0-9_\-\.:]+$`)
  - [ ] Disallow `shell=True` and enforce a 10-second timeout
- [ ] Implement `core/command_router.py`:
  - [ ] Intercept inputs starting with `/` before LLM processing
  - [ ] Handle `/models`, `/running`, `/unload <model>`, `/system`, `/clear`, and `/help`
- [ ] Build `pages/2_Hardware_&_Models.py`:
  - [ ] Display metric cards for RAM, CPU, and GPU
  - [ ] Display recommended models table with suitability badges
  - [ ] Interactive model pull interface with streaming progress bar (`POST /api/pull`)
- [ ] Integrate command router into `pages/1_Chat.py` so slash commands execute seamlessly in chat

---

## 3. Files to Create / Edit
- `core/system_info.py` — Hardware inspection routines
- `core/recommender.py` — Tier mapping and compatibility heuristic
- `core/subprocess_runner.py` — Hardened subprocess caller
- `core/command_router.py` — Pre-LLM slash command interpreter
- `pages/2_Hardware_&_Models.py` — Streamlit hardware dashboard and model manager
- `pages/1_Chat.py` — Update to intercept slash commands before calling LLM

---

## 4. Acceptance Criteria
1. Navigating to "Hardware & Models" displays accurate metrics for host RAM, CPU, and GPU.
2. The recommender marks models with clear status indicators:
   - 🟢 **Green (Smooth)**: Model memory footprint is well within free RAM.
   - 🟡 **Yellow (Borderline)**: Model fits in total RAM, but system may swap or run slowly.
   - 🔴 **Red (Heavy/OOM Risk)**: Model exceeds available memory; likely to trigger out-of-memory crash.
3. Users can enter a valid model name (e.g. `phi3:mini`) and click "Pull Model" to download it with an active progress bar.
4. Typing `/system` in the chat input prints live RAM and CPU stats as a system message without contacting the LLM.
5. Typing `/running` shows active models loaded in memory via `ollama ps`.
6. Typing `/unload <model>` unloads the specified model from memory using a safe subprocess call.
7. Attempting command injection (e.g., `/unload model; whoami` or `/unload model && dir`) is blocked by regex validation.

---

## 5. How to Test Manually
1. **Hardware Dashboard Test**:
   - Open "Hardware & Models" page.
   - Verify that RAM numbers match Windows Task Manager / Activity Monitor.
2. **Slash Command `/system` Test**:
   - Go to Chat page.
   - Type `/system` and press Enter.
   - Confirm immediate display of system specs without any LLM latency or token generation.
3. **Subprocess Whitelist & Security Test**:
   - Type `/unload "model; calc"` in chat.
   - Confirm that an "Invalid model name" error is returned immediately and no external program runs.
4. **Model Unload Test**:
   - Run a prompt so a model is loaded in memory.
   - Type `/running` to confirm the model is listed.
   - Type `/unload <model_name>` and confirm it exits memory.
   - Run `/running` again to verify memory is freed.

---

## 6. Interview Talking Points
- **Subprocess Security & Threat Modeling**: Discussing why `shell=True` is dangerous (command injection vulnerabilities), how parameterization via argument lists neutralizes shell meta-characters, and how strict regex input validation creates defense-in-depth.
- **Hardware-Aware AI Engineering**: Explaining quantization formats (Q4_K_M vs. FP16), memory estimation heuristics (params × precision + KV cache overhead), and why proactive hardware checks prevent catastrophic system freezes.
- **Pre-LLM Command Routing Pattern**: Designing an interceptor pattern where user input is evaluated and short-circuited before triggering expensive model inference.
