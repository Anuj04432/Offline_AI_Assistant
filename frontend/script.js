document.addEventListener('DOMContentLoaded', () => {
    // Configure marked to use highlight.js
    if (typeof marked !== 'undefined' && typeof hljs !== 'undefined') {
        marked.setOptions({
            highlight: function(code, lang) {
                const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                return hljs.highlight(code, { language }).value;
            },
            breaks: true
        });
    }

    const API_BASE = window.location.origin;

    // DOM Elements
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatContainer = document.getElementById('chatContainer');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const messagesWrapper = document.getElementById('messagesWrapper');
    const newChatBtn = document.getElementById('newChatBtn');
    const historyList = document.getElementById('historyList');
    const modelSelect = document.getElementById('modelSelect');
    const headerModelTitle = document.getElementById('headerModelTitle');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const connectionLed = document.getElementById('connectionLed');
    const connectionStatus = document.getElementById('connectionStatus');
    const systemSpecsPill = document.getElementById('systemSpecsPill');
    const specsSummaryText = document.getElementById('specsSummaryText');
    const refreshBtn = document.getElementById('refreshBtn');
    const exploreModelsBtn = document.getElementById('exploreModelsBtn');
    const backToChatBtn = document.getElementById('backToChatBtn');

    // View Containers
    const ollamaInstallView = document.getElementById('ollamaInstallView');
    const ollamaServiceView = document.getElementById('ollamaServiceView');
    const noModelsView = document.getElementById('noModelsView');
    const chatView = document.getElementById('chatView');

    // Onboarding buttons
    const recheckInstallBtn = document.getElementById('recheckInstallBtn');
    const retryServiceBtn = document.getElementById('retryServiceBtn');
    const fileUploadBtn = document.getElementById('fileUploadBtn');
    const hiddenFileInput = document.getElementById('hiddenFileInput');

    // Filter tabs
    const tabRecommended = document.getElementById('tabRecommended');
    const tabAll = document.getElementById('tabAll');

    // Memory Modal Elements
    const manageMemoryBtn = document.getElementById('manageMemoryBtn');
    const memoryModal = document.getElementById('memoryModal');
    const closeMemoryModalBtn = document.getElementById('closeMemoryModalBtn');
    const newMemoryInput = document.getElementById('newMemoryInput');
    const saveMemoryBtn = document.getElementById('saveMemoryBtn');
    const memoryList = document.getElementById('memoryList');

    let currentSessionId = null;
    let installedModels = [];
    let systemHardware = null;
    let allCatalogModels = [];
    let activeCatalogFilter = 'recommended';
    let isGenerating = false;

    // =====================================================================
    // VIEW ROUTING
    // =====================================================================

    function showView(viewId) {
        const views = [ollamaInstallView, ollamaServiceView, noModelsView, chatView];
        views.forEach(v => {
            if (v) v.style.display = 'none';
        });

        const active = document.getElementById(viewId);
        if (active) {
            active.style.display = 'flex';
        }

        // When switching back to chat, auto-scroll to bottom
        if (viewId === 'chatView') {
            scrollToBottom();
        }
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        });
    }

    function setConnectionState(state, label) {
        connectionLed.className = 'led';
        if (state === 'online') {
            connectionLed.classList.add('online');
            connectionStatus.textContent = label || 'ONLINE';
        } else if (state === 'warning') {
            connectionStatus.textContent = label || 'STOPPED';
        } else {
            connectionLed.classList.add('offline');
            connectionStatus.textContent = label || 'NOT INSTALLED';
        }
    }

    function badgeForModel(name) {
        if (!name) return 'Model';
        const n = name.toLowerCase();
        if (n.includes('coder')) return 'Code';
        if (n.includes('qwen')) return 'Fast';
        if (n.includes('mistral')) return 'Fast';
        if (n.includes('llama')) return 'Smart';
        if (n.includes('deepseek')) return 'Reason';
        if (n.includes('phi')) return 'Light';
        if (n.includes('gemma')) return 'Precise';
        return 'Local';
    }

    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    // =====================================================================
    // PROVIDER & HARDWARE DIAGNOSTICS
    // =====================================================================

    async function checkProviderStatus() {
        setConnectionState('warning', 'CHECKING...');
        try {
            const resp = await fetch(`${API_BASE}/api/status`);
            const data = await resp.json();

            // 1. Not installed
            if (!data.ollama_installed) {
                setConnectionState('offline', 'NOT INSTALLED');
                showView('ollamaInstallView');
                headerModelTitle.innerHTML = `Ollama <span class="model-badge">Not Installed</span>`;
                return;
            }

            // 2. Installed but service stopped
            if (!data.service_running) {
                setConnectionState('warning', 'SERVICE STOPPED');
                showView('ollamaServiceView');
                headerModelTitle.innerHTML = `Ollama <span class="model-badge">Stopped</span>`;
                return;
            }

            // 3. Service online: fetch hardware & models
            setConnectionState('online', `ONLINE (v${data.version || ''})`);
            await loadHardwareSpecs();
            await loadModels();

        } catch (err) {
            console.error('Failed to query status:', err);
            setConnectionState('offline', 'OFFLINE');
            showView('ollamaServiceView');
        }
    }

    async function loadHardwareSpecs() {
        try {
            const resp = await fetch(`${API_BASE}/api/hardware`);
            systemHardware = await resp.json();

            if (systemSpecsPill && specsSummaryText) {
                systemSpecsPill.style.display = 'flex';
                specsSummaryText.textContent = `${systemHardware.ram_total_gb} GB RAM • Tier ${systemHardware.hardware_tier}`;
            }
        } catch (err) {
            console.error('Failed to load hardware:', err);
        }
    }

    async function loadModels() {
        try {
            const resp = await fetch(`${API_BASE}/api/models`);
            const data = await resp.json();
            installedModels = data.models || [];

            // Case A: No models downloaded -> show hardware & recommender hub
            if (installedModels.length === 0) {
                showView('noModelsView');
                modelSelect.innerHTML = '<option value="">No models installed</option>';
                headerModelTitle.innerHTML = `No Models <span class="model-badge">Download One</span>`;
                await renderHardwareAndRecommendations();
                return;
            }

            // Case B: Models present -> populate dropdown and show chat
            modelSelect.innerHTML = '';
            installedModels.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m;
                opt.textContent = m;
                modelSelect.appendChild(opt);
            });

            // Auto-select default or first model
            const targetModel = data.default_model || installedModels[0];
            modelSelect.value = targetModel;
            headerModelTitle.innerHTML = `${targetModel} <span class="model-badge">${badgeForModel(targetModel)}</span>`;

            showView('chatView');
            fetchSessions();

        } catch (err) {
            console.error('Failed to load models:', err);
            showView('noModelsView');
            await renderHardwareAndRecommendations();
        }
    }

    // =====================================================================
    // HARDWARE & RECOMMENDATIONS RENDERER
    // =====================================================================

    async function renderHardwareAndRecommendations() {
        const specsGrid = document.getElementById('specsGrid');
        const summaryText = document.getElementById('hardwareSummaryText');

        if (!systemHardware) {
            await loadHardwareSpecs();
        }

        // Render hardware diagnostic cards
        if (specsGrid && systemHardware) {
            specsGrid.innerHTML = `
                <div class="spec-card">
                    <span class="spec-val">${systemHardware.ram_total_gb} GB</span>
                    <span class="spec-label">Total System RAM</span>
                </div>
                <div class="spec-card">
                    <span class="spec-val">${systemHardware.ram_available_gb} GB</span>
                    <span class="spec-label">Available Free RAM</span>
                </div>
                <div class="spec-card">
                    <span class="spec-val">${systemHardware.cpu_physical_cores} Cores / ${systemHardware.cpu_logical_cores}T</span>
                    <span class="spec-label">CPU Cores</span>
                </div>
                <div class="spec-card">
                    <span class="spec-val">${systemHardware.hardware_tier}</span>
                    <span class="spec-label">Hardware Tier</span>
                </div>
            `;
        }

        // Fetch recommendations from backend
        try {
            const resp = await fetch(`${API_BASE}/api/recommendations`);
            const data = await resp.json();

            if (summaryText) {
                summaryText.innerHTML = `
                    <strong>${data.summary}</strong><br>
                    <span style="font-size: 12px; color: var(--text-secondary); margin-top: 4px; display: inline-block;">
                        <i class="fa-solid fa-circle-info"></i> Suitability badges are calculated dynamically by comparing each model's memory footprint against your ${systemHardware.ram_total_gb} GB RAM.
                    </span>
                `;
            }

            allCatalogModels = data.models || [];
            filterAndDisplayModels();

        } catch (err) {
            console.error('Failed to fetch recommendations:', err);
        }
    }

    function filterAndDisplayModels() {
        const modelsGrid = document.getElementById('recommendedModelsGrid');
        if (!modelsGrid) return;

        let filtered = allCatalogModels;
        if (activeCatalogFilter === 'recommended') {
            filtered = allCatalogModels.filter(m => m.suitability === 'optimal' || m.suitability === 'compatible');
        }

        modelsGrid.innerHTML = '';
        filtered.forEach(model => {
            const card = document.createElement('div');
            card.className = 'model-card';

            const isAlreadyInstalled = installedModels.includes(model.id);
            const userRam = systemHardware ? systemHardware.ram_total_gb : 8.0;

            card.innerHTML = `
                <div class="model-card-top">
                    <div class="model-card-title">
                        <h4>${model.name}</h4>
                        <span class="badge badge-${model.badge_color}">${model.badge_label}</span>
                    </div>
                    <div class="model-meta-row">
                        <span><i class="fa-solid fa-download"></i> ${model.download_size}</span>
                        <span><i class="fa-solid fa-memory"></i> ${model.min_ram_gb}GB+ RAM</span>
                        <span><i class="fa-solid fa-tag"></i> ${model.tag}</span>
                    </div>
                    <p class="model-desc">${model.description}</p>
                    <div style="margin-top: 10px; font-size: 11px; font-family: var(--font-mono); color: var(--text-secondary); background: var(--bg-color); padding: 6px 10px; border-radius: 4px; border: 1px solid var(--border-color);">
                        <i class="fa-solid fa-calculator"></i> RAM Math: Requires ${model.recommended_ram_gb}GB | Your PC: ${userRam}GB (${model.suitability.toUpperCase()})
                    </div>
                </div>

                <div class="model-card-actions">
                    ${isAlreadyInstalled ? `
                        <button class="btn secondary-btn" disabled style="opacity: 0.7; justify-content: center;">
                            <i class="fa-solid fa-check"></i> Already Installed
                        </button>
                    ` : `
                        <button class="download-model-btn" data-model="${model.id}">
                            <i class="fa-solid fa-cloud-arrow-down"></i> Download Model (${model.download_size})
                        </button>
                        <div class="download-progress-container" id="prog-${model.id.replace(/[:.]/g, '-')}" style="display: none;">
                            <div class="download-progress-bar">
                                <div class="progress-fill" style="width: 0%;"></div>
                            </div>
                            <div class="progress-text">Preparing download...</div>
                        </div>
                    `}

                    <div class="copy-cmd-row">
                        <code>${model.pull_command}</code>
                        <button class="copy-btn" title="Copy CLI Command" onclick="navigator.clipboard.writeText('${model.pull_command}')">
                            <i class="fa-regular fa-copy"></i>
                        </button>
                    </div>
                </div>
            `;

            // Wire download button
            const dlBtn = card.querySelector('.download-model-btn');
            if (dlBtn) {
                dlBtn.addEventListener('click', () => {
                    const progContainer = card.querySelector(`#prog-${model.id.replace(/[:.]/g, '-')}`);
                    downloadModel(model.id, dlBtn, progContainer);
                });
            }

            modelsGrid.appendChild(card);
        });
    }

    // =====================================================================
    // MODEL DOWNLOADER (STREAMING PROGRESS)
    // =====================================================================

    async function downloadModel(modelId, btn, progressContainer) {
        btn.classList.add('downloading');
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Downloading...`;
        if (progressContainer) progressContainer.style.display = 'block';

        const fill = progressContainer ? progressContainer.querySelector('.progress-fill') : null;
        const text = progressContainer ? progressContainer.querySelector('.progress-text') : null;

        try {
            const response = await fetch(`${API_BASE}/api/pull`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelId }),
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const chunk = JSON.parse(line);
                        const status = chunk.status || '';
                        const pct = chunk.percent || 0;

                        if (fill) fill.style.width = `${pct}%`;
                        if (text) {
                            if (chunk.total > 0) {
                                text.textContent = `${status} ${pct}% (${formatBytes(chunk.completed)} / ${formatBytes(chunk.total)})`;
                            } else {
                                text.textContent = status;
                            }
                        }

                        if (chunk.done) {
                            if (text) text.textContent = 'Download Complete! Loading model...';
                            if (fill) fill.style.width = '100%';
                        }
                    } catch (e) {
                        // ignore malformed JSON chunk
                    }
                }
            }

            // Successfully downloaded
            btn.innerHTML = `<i class="fa-solid fa-circle-check"></i> Download Complete!`;
            setTimeout(async () => {
                await checkProviderStatus();
            }, 1000);

        } catch (err) {
            console.error('Model download error:', err);
            btn.classList.remove('downloading');
            btn.innerHTML = `<i class="fa-solid fa-rotate-left"></i> Retry Download`;
            if (text) text.textContent = `Download failed: ${err.message}`;
        }
    }

    // =====================================================================
    // CHAT SESSIONS & NAVIGATION
    // =====================================================================

    async function fetchSessions() {
        try {
            const resp = await fetch(`${API_BASE}/api/sessions`);
            const data = await resp.json();
            historyList.innerHTML = '';
            if (data.sessions && data.sessions.length > 0) {
                data.sessions.forEach(session => {
                    const li = document.createElement('li');
                    li.className = 'history-item';
                    if (session.session_id === currentSessionId) li.classList.add('active');
                    li.innerHTML = `<i class="fa-regular fa-message"></i> <span>${session.title}</span>`;
                    li.addEventListener('click', () => loadSession(session.session_id));
                    historyList.appendChild(li);
                });
            } else {
                historyList.innerHTML = '<div class="empty-log">No sessions logged yet</div>';
            }
        } catch (err) {
            console.error('Error fetching sessions:', err);
        }
    }

    async function loadSession(sessionId) {
        try {
            const resp = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
            if (!resp.ok) return;
            const data = await resp.json();

            currentSessionId = sessionId;
            showView('chatView'); // Explicitly transition to chat view

            welcomeScreen.style.display = 'none';
            messagesWrapper.style.display = 'flex';
            messagesWrapper.innerHTML = '';

            data.history.forEach(msg => {
                if (msg.role !== 'system') {
                    addMessageToUI(msg.role === 'assistant' ? parseMarkdown(msg.content) : msg.content, msg.role);
                }
            });

            scrollToBottom();
            fetchSessions();
            if (window.innerWidth <= 768) sidebar.classList.remove('open');
        } catch (err) {
            console.error('Error loading session:', err);
        }
    }

    function parseMarkdown(text) {
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }
        return text;
    }

    function addMessageToUI(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        const isAssistant = sender === 'assistant';
        const avatarLabel = isAssistant ? 'AI' : 'U';

        messageDiv.innerHTML = `
            <div class="message-inner">
                <div class="avatar">${avatarLabel}</div>
                <div class="message-content">${content}</div>
            </div>
        `;

        messagesWrapper.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }

    function createAssistantStreamingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-inner">
                <div class="avatar">AI</div>
                <div class="message-content"><span class="typing-cursor">▋</span></div>
            </div>
        `;
        messagesWrapper.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv.querySelector('.message-content');
    }

    // =====================================================================
    // REAL-TIME TOKEN STREAMING CHAT
    // =====================================================================

    async function sendMessageToBackend(text) {
        if (isGenerating) return;
        isGenerating = true;

        const selectedModel = modelSelect.value;
        if (!selectedModel) {
            addMessageToUI('Please select an active model first.', 'assistant');
            isGenerating = false;
            return;
        }

        const contentEl = createAssistantStreamingMessage();
        let fullResponse = '';

        try {
            const response = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    model: selectedModel,
                    session_id: currentSessionId,
                    stream: true,
                }),
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed || !trimmed.startsWith('data: ')) continue;
                    const eventData = trimmed.replace('data: ', '');

                    if (eventData === '[DONE]') {
                        break;
                    }

                    try {
                        const parsed = JSON.parse(eventData);
                        if (parsed.type === 'meta') {
                            currentSessionId = parsed.session_id;
                        } else if (parsed.type === 'token') {
                            fullResponse += parsed.token;
                            contentEl.innerHTML = parseMarkdown(fullResponse) + '<span class="typing-cursor">▋</span>';
                            scrollToBottom();
                        }
                    } catch (e) {
                        // ignore partial event parsing
                    }
                }
            }

            // Finished streaming: remove cursor
            contentEl.innerHTML = parseMarkdown(fullResponse);
            scrollToBottom();
            fetchSessions();

        } catch (err) {
            console.error('Chat error:', err);
            contentEl.innerHTML = `<span style="color: #eb5757;"><i class="fa-solid fa-triangle-exclamation"></i> Error communicating with local model: ${err.message}</span>`;
        } finally {
            isGenerating = false;
        }
    }

    function handleSend() {
        const text = messageInput.value.trim();
        if (!text || isGenerating) return;

        welcomeScreen.style.display = 'none';
        messagesWrapper.style.display = 'flex';

        addMessageToUI(text, 'user');

        messageInput.value = '';
        messageInput.style.height = 'auto';
        sendBtn.classList.remove('active');
        sendBtn.setAttribute('disabled', 'true');

        sendMessageToBackend(text);
    }

    // =====================================================================
    // PERSISTENT FRONTIER MEMORY MANAGEMENT
    // =====================================================================

    async function loadMemories() {
        try {
            const resp = await fetch(`${API_BASE}/api/memories`);
            const data = await resp.json();
            memoryList.innerHTML = '';

            if (data.memories && data.memories.length > 0) {
                data.memories.forEach(mem => {
                    const item = document.createElement('div');
                    item.className = 'memory-item';
                    item.innerHTML = `
                        <span>${mem.fact}</span>
                        <button class="memory-del-btn" title="Delete memory" data-id="${mem.id}">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    `;
                    item.querySelector('.memory-del-btn').addEventListener('click', async () => {
                        await deleteMemory(mem.id);
                    });
                    memoryList.appendChild(item);
                });
            } else {
                memoryList.innerHTML = '<div class="empty-memory">No memories saved yet. Add a preference above to test cross-session memory!</div>';
            }
        } catch (err) {
            console.error('Failed to load memories:', err);
        }
    }

    async function addMemory(fact) {
        if (!fact.trim()) return;
        try {
            await fetch(`${API_BASE}/api/memories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fact: fact.trim() }),
            });
            newMemoryInput.value = '';
            await loadMemories();
        } catch (err) {
            console.error('Failed to save memory:', err);
        }
    }

    async function deleteMemory(memId) {
        try {
            await fetch(`${API_BASE}/api/memories/${memId}`, { method: 'DELETE' });
            await loadMemories();
        } catch (err) {
            console.error('Failed to delete memory:', err);
        }
    }

    // =====================================================================
    // EVENT LISTENERS & WIRING
    // =====================================================================

    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim() !== '') {
            sendBtn.classList.add('active');
            sendBtn.removeAttribute('disabled');
        } else {
            sendBtn.classList.remove('active');
            sendBtn.setAttribute('disabled', 'true');
        }
    });

    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim() !== '') handleSend();
        }
    });

    sendBtn.addEventListener('click', () => {
        if (messageInput.value.trim() !== '') handleSend();
    });

    newChatBtn.addEventListener('click', () => {
        currentSessionId = null;
        welcomeScreen.style.display = 'flex';
        messagesWrapper.style.display = 'none';
        messagesWrapper.innerHTML = '';
        showView('chatView');
        fetchSessions();
        if (window.innerWidth <= 768) sidebar.classList.remove('open');
    });

    modelSelect.addEventListener('change', (e) => {
        const sel = e.target.value;
        if (sel) {
            headerModelTitle.innerHTML = `${sel} <span class="model-badge">${badgeForModel(sel)}</span>`;
        }
    });

    menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    if (recheckInstallBtn) recheckInstallBtn.addEventListener('click', checkProviderStatus);
    if (retryServiceBtn) retryServiceBtn.addEventListener('click', checkProviderStatus);
    if (refreshBtn) refreshBtn.addEventListener('click', checkProviderStatus);

    // Hardware Hub Navigation
    if (exploreModelsBtn) {
        exploreModelsBtn.addEventListener('click', async () => {
            showView('noModelsView');
            await renderHardwareAndRecommendations();
            if (window.innerWidth <= 768) sidebar.classList.remove('open');
        });
    }

    if (backToChatBtn) {
        backToChatBtn.addEventListener('click', () => {
            showView('chatView');
        });
    }

    // Catalog filter tabs
    if (tabRecommended && tabAll) {
        tabRecommended.addEventListener('click', () => {
            tabRecommended.classList.add('active');
            tabAll.classList.remove('active');
            activeCatalogFilter = 'recommended';
            filterAndDisplayModels();
        });

        tabAll.addEventListener('click', () => {
            tabAll.classList.add('active');
            tabRecommended.classList.remove('active');
            activeCatalogFilter = 'all';
            filterAndDisplayModels();
        });
    }

    // Memory Modal Wiring
    if (manageMemoryBtn && memoryModal) {
        manageMemoryBtn.addEventListener('click', async () => {
            memoryModal.style.display = 'flex';
            await loadMemories();
            if (window.innerWidth <= 768) sidebar.classList.remove('open');
        });
    }

    if (closeMemoryModalBtn && memoryModal) {
        closeMemoryModalBtn.addEventListener('click', () => {
            memoryModal.style.display = 'none';
        });
    }

    if (memoryModal) {
        memoryModal.addEventListener('click', (e) => {
            if (e.target === memoryModal) {
                memoryModal.style.display = 'none';
            }
        });
    }

    if (saveMemoryBtn && newMemoryInput) {
        saveMemoryBtn.addEventListener('click', () => {
            addMemory(newMemoryInput.value);
        });

        newMemoryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                addMemory(newMemoryInput.value);
            }
        });
    }

    // Document attachment
    if (fileUploadBtn && hiddenFileInput) {
        fileUploadBtn.addEventListener('click', () => hiddenFileInput.click());
        hiddenFileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            welcomeScreen.style.display = 'none';
            messagesWrapper.style.display = 'flex';
            addMessageToUI(`[Uploading file: ${file.name}...]`, 'user');

            const formData = new FormData();
            formData.append('file', file);
            if (currentSessionId) formData.append('session_id', currentSessionId);
            formData.append('model', modelSelect.value);

            try {
                const resp = await fetch(`${API_BASE}/upload`, {
                    method: 'POST',
                    body: formData,
                });
                const data = await resp.json();
                if (data.session_id) currentSessionId = data.session_id;
                addMessageToUI(parseMarkdown(data.response || 'File processed.'), 'assistant');
                fetchSessions();
            } catch (err) {
                addMessageToUI(`Error uploading file: ${err.message}`, 'assistant');
            }
        });
    }

    // =====================================================================
    // INITIALIZATION
    // =====================================================================
    checkProviderStatus();
});
