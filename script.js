async function sendMessage() {
    const input = document.getElementById("input");
    const chat = document.getElementById("chat");

    const msg = input.value;
    if (!msg) return;

    chat.innerHTML += `<p class="user">You: ${msg}</p>`;
    input.value = "";

    const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let botMsg = document.createElement("p");
    botMsg.className = "bot";
    botMsg.textContent = "Bot: ";
    chat.appendChild(botMsg);

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        botMsg.textContent += decoder.decode(value);
        chat.scrollTop = chat.scrollHeight;
    }
}