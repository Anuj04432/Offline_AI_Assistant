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

    let currentSessionId = null;

    // Initialize
    fetchModels();
    fetchSessions();

    async function fetchModels() {
        try {
            const response = await fetch('http://localhost:8000/models');
            const data = await response.json();
            if (data.models && data.models.length > 0) {
                modelSelect.innerHTML = '';
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    modelSelect.appendChild(option);
                });
                modelSelect.dispatchEvent(new Event('change'));
            } else {
                modelSelect.innerHTML = '<option value="">No models found</option>';
                headerModelTitle.innerHTML = `No Models <span class="model-badge">Error</span>`;
            }
        } catch (error) {
            console.error('Error fetching models:', error);
            modelSelect.innerHTML = '<option value="">Server offline</option>';
            headerModelTitle.innerHTML = `Offline <span class="model-badge">Error</span>`;
        }
    }

    async function fetchSessions() {
        try {
            const response = await fetch('http://localhost:8000/sessions');
            const data = await response.json();
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
                historyList.innerHTML = '<div style="padding:10px; color:#b4b4b4; font-size:12px;">No recent chats</div>';
            }
        } catch (error) {
            console.error('Error fetching sessions:', error);
        }
    }

    async function loadSession(sessionId) {
        try {
            const response = await fetch(`http://localhost:8000/sessions/${sessionId}`);
            if (!response.ok) return;
            const data = await response.json();
            
            currentSessionId = sessionId;
            welcomeScreen.style.display = 'none';
            messagesWrapper.style.display = 'flex';
            messagesWrapper.innerHTML = '';
            
            data.history.forEach(msg => {
                // skip system messages
                if (msg.role !== 'system') {
                    addMessageToUI(msg.role === 'assistant' ? parseMarkdown(msg.content) : msg.content, msg.role);
                }
            });
            
            fetchSessions(); // refresh active state
            
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
            }
        } catch (error) {
            console.error('Error loading session:', error);
        }
    }

    modelSelect.addEventListener('change', (e) => {
        const selectedModel = e.target.value;
        let badge = 'Default';
        if (selectedModel.includes('mistral')) badge = 'Fast';
        if (selectedModel.includes('llama')) badge = 'Smart';
        headerModelTitle.innerHTML = `${selectedModel} <span class="model-badge">${badge}</span>`;
    });

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
        fetchSessions();
        if (window.innerWidth <= 768) sidebar.classList.remove('open');
    });

    menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));

    function handleSend() {
        const text = messageInput.value.trim();
        if (!text) return;

        welcomeScreen.style.display = 'none';
        messagesWrapper.style.display = 'flex';

        addMessageToUI(text, 'user');

        messageInput.value = '';
        messageInput.style.height = 'auto';
        sendBtn.classList.remove('active');
        sendBtn.setAttribute('disabled', 'true');

        sendMessageToBackend(text);
    }

    function addMessageToUI(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        const isBot = sender === 'assistant' || sender === 'bot';
        const avatarIcon = isBot ? '<i class="fa-solid fa-robot"></i>' : 'U';
        
        messageDiv.innerHTML = `
            <div class="message-inner">
                <div class="message-avatar">${avatarIcon}</div>
                <div class="message-content">${content}</div>
            </div>
        `;
        messagesWrapper.appendChild(messageDiv);
        chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
        return messageDiv;
    }

    function showTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message bot typing-msg';
        indicatorDiv.id = 'typingIndicator';
        indicatorDiv.innerHTML = `
            <div class="message-inner">
                <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="dot"></div><div class="dot"></div><div class="dot"></div>
                    </div>
                </div>
            </div>
        `;
        messagesWrapper.appendChild(indicatorDiv);
        chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
        return indicatorDiv;
    }

    async function sendMessageToBackend(message) {
        const typingIndicator = showTypingIndicator();
        const selectedModel = modelSelect.value;
        
        let fullMessage = message;
        if (extractedFileText) {
            fullMessage = `[File Content]:\n${extractedFileText}\n\n[User Message]:\n${message}`;
            extractedFileText = "";
            document.getElementById('fileUploadBtn').style.color = '';
        }
        
        try {
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: fullMessage, 
                    model: selectedModel,
                    session_id: currentSessionId 
                })
            });
            
            const data = await response.json();
            typingIndicator.remove();
            
            if (response.ok) {
                currentSessionId = data.session_id; // update session id
                addMessageToUI(parseMarkdown(data.reply), 'assistant');
                fetchSessions(); // refresh history list
            } else {
                addMessageToUI(`Error: ${data.detail || "Something went wrong"}`, 'assistant');
            }
        } catch (error) {
            typingIndicator.remove();
            addMessageToUI("Sorry, I could not connect to the backend server. Is it running?", 'assistant');
            console.error('Error:', error);
        }
    }

    function parseMarkdown(text) {
        if (!text) return "";
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }
        // Fallback
        let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    // File Upload Logic
    let extractedFileText = "";
    const fileUploadBtn = document.getElementById('fileUploadBtn');
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.txt,.pdf';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);

    fileUploadBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        fileUploadBtn.style.color = '#10a37f';

        try {
            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                extractedFileText = data.extracted_text;
                addMessageToUI(`File attached: ${file.name}. It will be sent with your next message.`, 'bot');
            } else {
                addMessageToUI(`Failed to process file: ${data.detail}`, 'bot');
                fileUploadBtn.style.color = '';
            }
        } catch (error) {
            console.error('File upload error:', error);
            addMessageToUI("Error connecting to backend for file upload.", 'bot');
            fileUploadBtn.style.color = '';
        }
        fileInput.value = '';
    });

    const voiceBtn = document.getElementById('voiceBtn');
    voiceBtn.addEventListener('click', () => {
        addMessageToUI("Voice recording activated. (Requires backend integration)", 'bot');
    });
});
