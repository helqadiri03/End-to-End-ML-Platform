document.addEventListener('DOMContentLoaded', function() {
    // Get all necessary elements
    const chatButton = document.querySelector('.btn-outline-primary');
    const chatSection = document.querySelector('.chat-section');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.querySelector('.chat-messages');
    const fileInput = document.querySelector('.form-control.border-0');

    // Add click handler for Quick Visualization card
    const quickVisCard = document.querySelector('.workflow-card');
    quickVisCard.addEventListener('click', function() {
        window.location.href = '/visualization';
    });

    // Toggle chat section and start initial chat when chat button is clicked
    chatButton.addEventListener('click', function() {
        chatSection.style.display = chatSection.style.display === 'none' ? 'block' : 'none';
        
        // If chat is being shown and no messages exist, add initial greeting
        if (chatSection.style.display === 'block' && chatMessages.children.length === 0) {
            addMessage('Bot', 'Hello! How can I help you analyze your data today?');
        }
    });

    // Handle file input changes
    fileInput.addEventListener('change', function(e) {
        if (this.value) {
            addMessage('Bot', `I see you want to analyze "${this.value}". What would you like to know about this data?`);
        }
    });

    // Handle chat form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage('You', message);
        
        // Show loading message
        const loadingId = showLoadingMessage();

        // Send message to server
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading message
            removeLoadingMessage(loadingId);
            
            if (data.status === 'success') {
                addMessage('Bot', data.response);
            } else {
                addMessage('Bot', 'Sorry, I encountered an error.');
            }
        })
        .catch(error => {
            // Remove loading message
            removeLoadingMessage(loadingId);
            
            console.error('Error:', error);
            addMessage('Bot', 'Sorry, I encountered an error.');
        });

        messageInput.value = '';
    });

    function addMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message p-2 mb-2 ' + 
            (sender === 'You' ? 'text-end bg-light' : 'bg-primary text-white');
        messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showLoadingMessage() {
        const loadingDiv = document.createElement('div');
        const loadingId = 'loading-' + Date.now();
        loadingDiv.id = loadingId;
        loadingDiv.className = 'message p-2 mb-2 bg-primary text-white';
        loadingDiv.innerHTML = '<strong>Bot:</strong> Thinking...';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return loadingId;
    }

    function removeLoadingMessage(loadingId) {
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
});

