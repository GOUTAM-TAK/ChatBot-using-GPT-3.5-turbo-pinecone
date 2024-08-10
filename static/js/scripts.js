document.addEventListener('DOMContentLoaded', (event) => {
    const chatbox = document.getElementById('chatbox');
    const imageUrl = '/static/images/chatbox_bg.jpg'; // Correct URL for the image
    chatbox.style.backgroundImage = `url('${imageUrl}')`;
    chatbox.style.backgroundSize = 'cover'; // Ensure the image covers the chatbox

    // Fetch and display sources when the page loads
    fetchSources();
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
        // Refresh sources after adding file
        fetchSources();
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
        // Refresh sources after deleting file
        fetchSources();
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

function fetchSources() {
    const sourcesList = document.getElementById('sourcesList');
    sourcesList.innerHTML = '<p>Loading sources...</p>'; // Show loading message

    fetch('/listsources/')
    .then(response => {
        if (!response.ok) {
            throw new Error(`Network response was not ok. Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        sourcesList.innerHTML = ''; // Clear loading message

        // Check if 'sourcesList' is present in data
        if (!data.sourcesList) {
            throw new Error('Invalid response format. Missing "sourcesList" field.');
        }

        // Create checkboxes for each source
        data.sourcesList.forEach(source => {
            const label = document.createElement('label');
            label.textContent = source;

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = source;
            checkbox.classList.add('source-checkbox');

            label.appendChild(checkbox);
            sourcesList.appendChild(label);
            sourcesList.appendChild(document.createElement('br')); // Add line break
        });
    })
    .catch(error => {
        console.error('Error fetching sources:', error);
        sourcesList.innerHTML = '<p>Failed to load sources. Please try again later.</p>'; // Show error message
    });
}