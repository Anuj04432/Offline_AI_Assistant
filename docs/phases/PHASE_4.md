# Phase 4: Settings, Personas, Eco Mode, Live Monitor & Context Trimming

## 1. Goal
Provide power users and resource-constrained users with granular controls over LLM behavior and system resource consumption.
Introduce configurable generation parameters, pre-built system personas, an "Eco Mode" for conserving battery and memory on low-spec devices, a real-time sidebar resource monitor, and smart context trimming to avoid context window degradation.

---

## 2. Existing Code Reused in Phase 4
- **`backend/main.py` (System Message & `num_predict`)**: Reuses the system prompt pattern and token prediction limit (`"num_predict": 400`) from `backend/main.py`, generalizing them into dynamic user personas and Eco Mode resource boundaries.

---

## 3. Tasks Checklist
- [ ] Implement Settings Storage in `core/db.py`:
  - [ ] `get_setting(key, default=None) -> Any`
  - [ ] `set_setting(key, value) -> None`
- [ ] Build `pages/3_Settings.py`:
  - [ ] Generation parameters controls: Temperature (0.0 to 1.5), Top-P (0.1 to 1.0), Max Tokens (64 to 2048)
  - [ ] Persona selector with preset system prompts:
    - **General Assistant**: Balanced, helpful, concise
    - **Senior Software Engineer**: Direct, clean code, no fluff, explains trade-offs
    - **Academic Tutor**: Step-by-step Socratic explanations
    - **Creative Writer**: Rich descriptive language and narrative focus
  - [ ] Custom persona editor (free-form system prompt textarea)
  - [ ] "Eco Mode" toggle with descriptive explainer
  - [ ] "Unload Active Model" button to free RAM on demand
- [ ] Implement Context Management in `core/ollama_client.py`:
  - [ ] Token estimation heuristic (character-to-token ratio approximation)
  - [ ] Sliding context window: preserves system prompt + latest N message turns to avoid context overflow
- [ ] Implement Live Resource Monitor:
  - [ ] Add compact CPU and RAM usage gauge/progress bars in the Streamlit sidebar across all pages
- [ ] Implement Eco Mode adjustments:
  - [ ] Caps `max_tokens` to 256
  - [ ] Restricts context window to the last 4 turns
  - [ ] Lowers generation concurrency

---

## 3. Files to Create / Edit
- `core/config.py` — Default generation parameters and persona prompt templates
- `core/db.py` — Settings persistence methods
- `core/ollama_client.py` — Support context window trimming and custom parameters in `/api/chat` payload
- `pages/3_Settings.py` — Comprehensive configuration dashboard
- `pages/1_Chat.py` — Inject active persona system prompt, context trimming, and sidebar resource gauges

---

## 4. Acceptance Criteria
1. Changing generation parameters (e.g. lowering temperature to 0.1) alters model output behavior deterministically.
2. Selecting the "Senior Software Engineer" persona injects the engineering system prompt, causing the model to respond in the persona's style.
3. Custom system prompts entered in Settings persist in `localmind.db` and apply to subsequent chats.
4. When "Eco Mode" is enabled:
   - Output length is capped.
   - Long conversation histories are automatically trimmed to preserve memory and speed up inference.
5. The sidebar displays live indicators for RAM and CPU usage that update during app interaction.
6. Clicking "Unload Model" frees RAM immediately and confirms memory release via `psutil`.

---

## 5. How to Test Manually
1. **Persona Verification**:
   - Set persona to "Senior Software Engineer" in Settings.
   - Ask in Chat: `"How should I structure a Python project?"`
   - Verify the response focuses on clean architectures, typing, and testing without conversational filler.
2. **Temperature Control Test**:
   - Set temperature to `0.0` and ask the same factual math/logic question twice; verify near-identical answers.
   - Set temperature to `1.2` and ask a creative story prompt; verify diverse vocabulary.
3. **Eco Mode Context Trimming Test**:
   - Enable Eco Mode.
   - Conduct a 10-turn conversation.
   - Inspect the outbound payload to ensure only the system prompt and latest turns are transmitted, preventing sluggish generation.
4. **Live RAM Monitor Test**:
   - Observe the sidebar RAM indicator before and during model generation.
   - Confirm RAM utilization rises when the model loads into memory and drops when "Unload Model" is clicked.

---

## 6. Interview Talking Points
- **Context Window Management & KV Cache Bloat**: Why sending unbounded conversation history degrades local inference speed (quadratic attention complexity and KV cache memory bloat), and how sliding-window trimming mitigates memory exhaustion on consumer hardware.
- **System Prompt Steering**: How system prompts act as steering vectors in instruction-tuned models, and how separating personas from conversational turn history provides flexible customization.
- **Resource-Aware Engineering (Eco Mode)**: Designing proactive software throttles for laptops on battery power or machines with shared memory, prioritizing stability and responsiveness over maximal output length.
