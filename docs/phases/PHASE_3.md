# Phase 3: SQLite Persistent Chats, Search & Export

## 1. Goal
Upgrade LocalMind from ephemeral in-memory sessions to persistent relational storage using SQLite.
Users can seamlessly revisit past conversations, rename them, delete unwanted chats, search chat history for keywords, and export transcripts into clean Markdown (`.md`) or structured JSON files.

---

## 2. Existing Code Reused in Phase 3
- **`backend/main.py` (`sessions` & `/sessions`)**: Reuses the concept of session IDs and auto-generating conversation titles from the first message snippet (`content[:30]`). Upgrades the fragile in-memory Python dictionary to a durable SQLite database (`./localmind.db`).
- **`frontend/script.js` (`fetchSessions` & `loadSession`)**: Reuses session selection and history restoration workflows, migrating them into native Streamlit sidebar state.

---

## 3. Tasks Checklist
- [ ] Implement `core/db.py`:
  - [ ] Initialize SQLite database (`localmind.db`) with WAL mode and foreign key constraints
  - [ ] Implement schema creation (`conversations`, `messages`, `settings`, `usage_stats`)
  - [ ] `create_conversation(title, model_name, system_prompt) -> str`
  - [ ] `list_conversations(search_query=None) -> list[dict]`
  - [ ] `get_conversation_messages(conversation_id) -> list[dict]`
  - [ ] `add_message(conversation_id, role, content, token_count) -> str`
  - [ ] `rename_conversation(conversation_id, new_title) -> bool`
  - [ ] `delete_conversation(conversation_id) -> bool`
  - [ ] `export_conversation(conversation_id, format='md'|'json') -> str`
- [ ] Update `pages/1_Chat.py`:
  - [ ] Display conversation history list in the sidebar with active highlight
  - [ ] Add conversation title auto-generation from the first user prompt (first 30 characters)
  - [ ] Add edit modal/expander for renaming conversation titles
  - [ ] Add delete confirmation button for each conversation
  - [ ] Add real-time search input in sidebar to filter conversations by title or message content
  - [ ] Add "Export Chat" dropdown offering Markdown and JSON download buttons (`st.download_button`)
- [ ] Ensure thread-safe SQLite access across Streamlit reruns

---

## 3. Files to Create / Edit
- `core/db.py` — Database connection management, schema initialization, and CRUD functions
- `pages/1_Chat.py` — Sidebar history integration, conversation switching, search, and export
- `tests/test_db.py` — Comprehensive unit tests verifying database operations and cascade deletes

---

## 4. Acceptance Criteria
1. Conversations and messages are saved to `./localmind.db` as they occur.
2. Restarting the Streamlit application retains all previous chat sessions in the sidebar.
3. Clicking a past conversation in the sidebar immediately loads its entire message history into the chat view.
4. Users can rename a conversation title, and the change persists immediately in the sidebar.
5. Deleting a conversation removes it and cascades the deletion to all associated messages in the database.
6. Typing into the sidebar search box dynamically filters the list of displayed conversations based on matching titles or message content.
7. Clicking "Export as Markdown" downloads a `.md` file with clean headers and timestamps.
8. Clicking "Export as JSON" downloads a valid JSON payload containing the complete transcript schema.

---

## 5. How to Test Manually
1. **Persistence Across Restart Test**:
   - Start a new conversation and send 3 back-and-forth messages.
   - Stop Streamlit (`Ctrl+C`) and restart it with `streamlit run app.py`.
   - Verify that the chat appears in the sidebar and clicking it restores the exact message transcript.
2. **Rename & Delete Test**:
   - Rename a chat to `"Architecture Discussion"`.
   - Verify the sidebar title updates immediately.
   - Delete the chat and verify it vanishes from the database and UI.
3. **Keyword Search Test**:
   - Create two chats: one mentioning `"Python decorators"` and another mentioning `"Docker Compose"`.
   - Enter `"decorators"` in the search box.
   - Confirm only the relevant chat remains visible in the sidebar.
4. **Export Format Test**:
   - Export a chat as Markdown and inspect the file: ensure headers, roles, and code fences are preserved.
   - Export as JSON and validate the file with `json.loads()`.

---

## 6. Interview Talking Points
- **SQLite Concurrency & WAL Mode**: Why SQLite is ideal for single-user local applications, how Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) allows concurrent readers while a write is occurring, and how SQLite handles multi-threaded Streamlit requests via connection isolation or context managers.
- **Relational Integrity with Foreign Keys**: Using `ON DELETE CASCADE` so message cleanup is atomic and leaves no orphaned records when a parent conversation is removed.
- **Data Portability as a Feature**: The importance of data sovereignty and user trust in offline AI tools, giving users immediate ownership of their data through standardized Markdown and JSON export formats.
