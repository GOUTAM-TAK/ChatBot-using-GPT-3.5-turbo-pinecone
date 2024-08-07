document.addEventListener('DOMContentLoaded', (event) => {
    const chatbox = document.getElementById('chatbox');
    const imageUrl = '/static/images/chatbox_bg.jpg'; // Correct URL for the image
    chatbox.style.backgroundImage = `url('${imageUrl}')`;
    chatbox.style.backgroundSize = 'cover'; // Ensure the image covers the chatbox
});

function clearMessages() {
    document.getElementById('uploadResult').innerText = '';
    document.getElementById('fileList').innerText = '';
    document.getElementById('deleteResult').innerText = '';
}

function sendPrompt() {
    clearMessages();
    const prompt = document.getElementById('chatInput').value;
    if (!prompt) return;  // Ensure prompt is not empty

    fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: prompt })
    })
    .then(response => response.json())
    .then(data => {
        const chatbox = document.getElementById('chatbox');
        const userMessage = document.createElement('div');
        userMessage.classList.add('chat-message', 'user-message');
        userMessage.innerText = prompt;
        chatbox.appendChild(userMessage);

        const botMessage = document.createElement('div');
        botMessage.classList.add('chat-message', 'bot-message');
        if (data.response) {
            botMessage.innerText = Array.isArray(data.response) ? data.response.join("\n") : data.response;
        } else if (data.error) {
            botMessage.innerText = data.error;
        } else {
            botMessage.innerText = 'No response from server.';
        }
        chatbox.appendChild(botMessage);

        document.getElementById('chatInput').value = '';  // Clear the input field
        chatbox.scrollTop = chatbox.scrollHeight;  // Scroll to the bottom
    })
    .catch(error => console.error('Error:', error));
}

function addDataset() {
    clearMessages();
    const fileInput = document.getElementById('file');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch('/uploadfile/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('uploadResult').innerText = data.message;
    })
    .catch(error => console.error('Error:', error));
}

function listFiles() {
    clearMessages();
    fetch('/listfiles/')
    .then(response => response.json())
    .then(data => {
        const fileList = document.getElementById('fileList');
        fileList.innerText = data.files.join('\n');
    })
    .catch(error => console.error('Error:', error));
}

function deleteFile() {
    clearMessages();
    const filename = document.getElementById('deleteFileName').value;
    fetch(`/deletefile/${filename}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('deleteResult').innerText = data.message;
    })
    .catch(error => console.error('Error:', error));
}

function downloadChatAsPDF() {
    const { jsPDF } = window.jspdf;
    const chatbox = document.getElementById('chatbox');
    if (!chatbox) {
        console.error('Chatbox element not found!');
        return;
    }
    const messages = chatbox.innerText;
    if (!messages) {
        console.error('No messages to download!');
        return;
    }
    const doc = new jsPDF();
    doc.text(messages, 10, 10);
    doc.save('chat_history.pdf');
}
