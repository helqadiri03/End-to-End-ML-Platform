async function uploadDataset() {
    const fileInput = document.getElementById('datasetFile');
    if (!fileInput.files.length) {
        alert("Veuillez sélectionner un fichier CSV.");
        return;
    }
    const formData = new FormData();
    formData.append('datasetFile', fileInput.files[0]);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        const uploadResponse = document.getElementById('uploadResponse');
        uploadResponse.classList.remove('hidden');
        
        if (response.ok) {
            uploadResponse.textContent = data.message;
        } else {
            uploadResponse.textContent = data.error || 'Erreur lors de l\'upload.';
        }
    } catch (error) {
        console.error(error);
    }
}

function appendMessage(role, text) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageElement = document.createElement('div');
    messageElement.className = 'p-3 rounded';

    if (role === 'user') {
        messageElement.classList.add('bg-blue-100', 'text-blue-900');
        messageElement.textContent = "Vous: " + text;
    } else if (role === 'assistant') {
        messageElement.classList.add('bg-green-100', 'text-green-900');
        messageElement.textContent = "Assistant: " + text;
    } else {
        // Pour les erreurs ou autres
        messageElement.classList.add('bg-red-100', 'text-red-900');
        messageElement.textContent = "Erreur: " + text;
    }

    chatMessages.appendChild(messageElement);
    // Scroller en bas pour voir le dernier message
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fonction pour envoyer un prompt
function sendPrompt() {
    const userPrompt = document.getElementById('userPrompt').value;

    fetch('/api/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userPrompt })
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            document.getElementById('result').innerText = data.response;
        } else if (data.error) {
            document.getElementById('result').innerText = "Erreur: " + data.error;
        }
    })
    .catch(error => console.error('Erreur:', error));
}

// Fonction pour exécuter le code
function executeCode() {
    const code = document.getElementById('result').innerText;

    fetch('/api/execute_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
    })
    .then(response => response.json())
    .then(data => {
        if (data.result) {
            document.getElementById('executionResult').innerHTML = data.result;
        } else if (data.error) {
            document.getElementById('executionResult').innerText = "Erreur: " + data.error;
        }
    })
    .catch(error => console.error('Erreur:', error));
}

document.getElementById("download-btn").addEventListener("click", function () {
    fetch("/api/download_dataset", { method: "GET" })
        .then(response => {
            if (!response.ok) {
                alert("Erreur lors du téléchargement du fichier.");
                return;
            }
            return response.blob();
        })
        .then(blob => {
            if (blob) {
                // Créer un lien temporaire pour déclencher le téléchargement
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.style.display = "none";
                a.href = url;
                a.download = "modified_dataset.csv";
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            }
        })
        .catch(error => {
            console.error("Erreur :", error);
            alert("Une erreur est survenue lors du téléchargement.");
        });
});
