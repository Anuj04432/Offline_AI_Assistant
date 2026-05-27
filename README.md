# 💬 Offline ChatGPT Clone (Ollama + Frontend)

A complete **ChatGPT-like offline AI assistant** powered by **Ollama** and a modern frontend interface.

This project runs **fully offline** using local LLMs — no OpenAI API or internet connection required after setup.

---

# 🚀 Features

- 🌐 Modern ChatGPT-style UI
- 🧠 Fully Offline AI using Ollama
- ⚡ Fast local response generation
- 🗂️ Chat history sidebar
- ➕ New Chat support
<!-- - 🎨 Dark theme interface -->
- 🤖 Multiple model selection
- 📎 File upload button (UI)
- 🎤 Microphone button (UI)
- 🔄 Real-time chat rendering
- 📱 Responsive design
- 🔌 Backend-ready architecture
- 📳 Models-used:-mistral,gemma and ph6


---

# 🧠 Tech Stack

## Frontend
- HTML5
- CSS3
- JavaScript

## Backend
- Python / Flask  

## AI Runtime
- Ollama

---

# 📁 Project Structure

```bash
Offline_AI_Assistant/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── routes/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── assets/
│
│
├── README.md
└── .gitignore
```

---

# 🛠️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/Anuj04432/Offline_AI_Assistant.git
cd Offline_AI_Assistant
```

---

# 📥 Install Ollama

Download and install Ollama from:

👉 https://ollama.com

Verify installation:

```bash
ollama --version
```

---

# 🤖 Download a Model

Example:

```bash
ollama pull mistral
```

Other supported models:

```bash
ollama pull llama2
ollama pull phi3
ollama pull gemma
```

---

# ⚙️ Backend Setup

## Using Python

### Create Virtual Environment

```bash
python -m venv myvenv
```

### Activate Virtual Environment

### Windows

```bash
myvenv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Backend

```bash
python app.py
```

---

# 🌐 Frontend Setup

Open:

```bash
frontend/index.html
```

or run using Live Server extension in VS Code.

---

# 🔌 Connect Frontend to Backend

In `script.js` update backend URL if needed:

```javascript
const API_URL = "http://localhost:5000/chat";
```

---

# ▶️ Running the Project

## Step 1

Start Ollama:

```bash
ollama serve
```

## Step 2

Run backend server:

```bash
python app.py
```

## Step 3

Open frontend in browser.

---

# 🧠 Example Ollama API Request

```python
import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "mistral",
        "prompt": "Hello"
    }
)

print(response.json())
```

---

# 🎨 UI Features

- ChatGPT-like layout
- Sidebar navigation
- Smooth scrolling
- Typing animation
- Markdown-style messages
- Mobile responsive UI
- Dynamic chat rendering

<!-- ---

# 📸 Screenshots

## Main Interface

Add screenshots inside:

```bash
screenshots/
```

Example:

```bash
screenshots/main-ui.png
```

--- -->

# 📌 Future Improvements

- ✅ Voice input support
- ✅ File processing
- ✅ Chat export
- ✅ Markdown rendering
- ✅ Streaming responses
- ✅ Local database storage
- ✅ Multi-chat sessions
- ✅ Syntax highlighting
- ✅ Electron desktop app
- ✅️ Multiple devices UI
---

# 🛡️ Privacy

This project is completely offline.

- No cloud API
- No data collection
- No internet dependency
- Full local execution

Your chats never leave your device.

---

# 🤝 Contributing

Pull requests are welcome.

For major changes, open an issue first to discuss improvements.

---

# 📜 License

This project is licensed under the MIT License.

---

# ⭐ Support

If you like this project:

- ⭐ Star the repository
- 🍴 Fork the project
- 🧠 Improve the UI
- 🚀 Add new features

---

# 👨‍💻 Author

### Anuj Wagmore

GitHub:
https://github.com/Anuj04432

---

# 🔥 Offline AI Powered by Ollama

Run powerful AI models locally with complete privacy and zero API costs.