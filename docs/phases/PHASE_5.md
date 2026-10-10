# Phase 5: Optional Cloud API Key Mode + Quota Fallback + Privacy Warning

## 1. Goal
Provide an optional cloud fallback for users with hardware too constrained to run capable local models, or for when complex tasks demand Frontier model capabilities.
Maintain uncompromising privacy hygiene:
- Users supply their own API key (stored strictly locally).
- Prominent privacy warnings alert users whenever prompts are transmitted over the internet.
- A local usage counter tracks token expenditures and enforces a configurable quota limit.

---

## 2. Existing Code Reused in Phase 5
- **`core/ollama_client.py`**: Wraps the proven offline Ollama streaming implementation into an `OllamaProvider` implementing `BaseLLMProvider`, allowing seamless switching to `OpenAICompatibleProvider`.

---

## 3. Tasks Checklist
- [ ] Implement Provider Abstraction in `core/providers.py`:
  - [ ] Define `BaseLLMProvider` abstract protocol:
    - `stream_chat(messages, model, options) -> Generator[str, None, None]`
    - `check_health() -> bool`
    - `get_available_models() -> list[str]`
  - [ ] Implement `OllamaProvider(BaseLLMProvider)` (100% offline default)
  - [ ] Implement `OpenAICompatibleProvider(BaseLLMProvider)`:
    - Interacts with OpenAI or any OpenAI-compatible API endpoint (OpenRouter, Groq, local vLLM)
    - Consumes user-provided API key from local storage/env
- [ ] Security & Key Hygiene:
  - [ ] Keys are entered via `st.text_input(type="password")`
  - [ ] Keys are stored only in the local SQLite database or `.env` file
  - [ ] Keys are NEVER echoed in the UI after saving
  - [ ] Keys are NEVER written to logs, stdout, or error stack traces
- [ ] Implement Local Usage Tracker & Quota in `core/db.py`:
  - [ ] Record prompt and completion token counts in `usage_stats` table
  - [ ] Calculate cumulative tokens consumed under cloud provider
  - [ ] If quota threshold is crossed, trigger "Quota reached: add/upgrade your key or switch to local Ollama" alert
- [ ] Implement Explicit Privacy Warning Banner in `pages/1_Chat.py`:
  - [ ] When an online provider is selected, display an unmistakable warning banner:
    > ⚠️ **Cloud Mode Active**: Prompts are transmitted over the internet to an external provider. Data is no longer confined to your local machine.
- [ ] Add Provider Selector in `pages/3_Settings.py`:
  - [ ] Toggle between "Local Offline (Ollama)" and "Cloud Fallback (OpenAI-compatible)"
  - [ ] Configuration fields for Custom Base URL, API Key, and Model ID (e.g. `gpt-4o-mini`)

---

## 3. Files to Create / Edit
- `core/providers.py` — Provider protocol and implementations for Ollama and OpenAI-compatible endpoints
- `core/db.py` — Add token usage recording and quota aggregation functions
- `pages/3_Settings.py` — Provider selection, masked API key configuration, quota setting
- `pages/1_Chat.py` — Privacy warning header and dynamic provider routing
- `tests/test_providers.py` — Unit tests for provider interfaces and token counting

---

## 4. Acceptance Criteria
1. Switching to "Cloud Fallback" immediately renders the prominent privacy disclosure banner in the chat UI.
2. The user's API key is masked during entry and is never logged to disk or console.
3. Chat interactions stream tokens from the configured cloud endpoint seamlessly using the same `st.write_stream` UI pattern.
4. Token usage is accurately tallied in `usage_stats`.
5. Exceeding the user-defined quota halts further cloud requests with a friendly prompt to adjust the quota or revert to local Ollama.
6. Switching back to "Local Offline (Ollama)" hides the cloud warning banner and routes 100% of traffic to the local daemon without internet access.

---

## 5. How to Test Manually
1. **Offline Integrity Verification**:
   - In "Local Offline" mode, disconnect your Wi-Fi or unplug ethernet.
   - Send prompts; confirm that LocalMind continues chatting without any internet dependency.
2. **Cloud Fallback & Privacy Warning Test**:
   - Reconnect internet.
   - Enter a test API key in Settings and select Cloud mode.
   - Return to Chat; confirm the prominent amber privacy warning banner is clearly visible.
   - Send prompt; verify successful streaming from the external provider.
3. **Key Sanitization Check**:
   - Search the entire repository and log output for the entered key string.
   - Confirm the key only resides encrypted or stored in the local SQLite file.
4. **Quota Limit Enforcement**:
   - Set monthly quota limit to a very low number (e.g., 50 tokens).
   - Send a prompt that generates 60 tokens.
   - Verify that the next attempt triggers the "Quota Exceeded" guardrail.

---

## 6. Interview Talking Points
- **The Provider / Strategy Design Pattern**: How polymorphism allows seamless swapping between local offline engines and cloud providers without rewriting any frontend or UI interaction logic.
- **Privacy Disclosures in AI Products**: Ethical software engineering principles regarding data boundaries: ensuring users always have clear, unambiguous visibility into when their prompts leave their local device.
- **Defensive API Key Hygiene**: Best practices for handling secrets in client applications: masking UI inputs, preventing accidental inclusion in logging pipelines, and ensuring local storage isolation.
