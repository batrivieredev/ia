document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const chatContainer = document.getElementById('chat-container');
    const chatForm = document.getElementById('chat-form');
    const logoutButton = document.getElementById('logout-button');
    const modelSelect = document.getElementById('model-select');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('chat-messages');
    const charCounter = document.querySelector('.char-counter');
    const maxLength = parseInt(messageInput.getAttribute('maxlength')) || 2000;

    // Templates
    const messageTemplate = document.getElementById('message-template');
    const loadingTemplate = document.getElementById('loading-template');

    // Socket.IO
    let socket = null;

    // Event Listeners
    chatForm.addEventListener('submit', handleMessage);
    logoutButton.addEventListener('click', handleLogout);
    messageInput.addEventListener('input', handleInput);
    modelSelect.addEventListener('change', handleModelSelect);

    // Vérifier l'authentification
    checkAuth();

    async function checkAuth() {
        try {
            const response = await fetch('/api/auth/check');
            const data = await response.json();

            if (!data.authenticated) {
                window.location.href = '/login.html';
            } else {
                loadModels();
                initializeSocket();
            }
        } catch (error) {
            console.error('Erreur auth:', error);
            window.location.href = '/login.html';
        }
    }

    function initializeSocket() {
        socket = io({
            path: '/ws/socket.io'
        });

        socket.on('connect', () => {
            console.log('WebSocket connecté');
        });

        socket.on('chat_response', (data) => {
            const loadingElement = messagesContainer.querySelector('.loading')?.parentElement;
            if (loadingElement) {
                loadingElement.remove();
            }
            appendAssistantMessage(data.content);
        });

        socket.on('chat_done', () => {
            setFormState(false);
        });

        socket.on('chat_error', (error) => {
            console.error('Erreur chat:', error);
            const loadingElement = messagesContainer.querySelector('.loading')?.parentElement;
            if (loadingElement) {
                loadingElement.remove();
            }
            appendAssistantMessage("Une erreur s'est produite");
            setFormState(false);
        });
    }

    async function handleLogout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            if (socket) {
                socket.disconnect();
            }
            window.location.href = '/login.html';
        } catch (error) {
            console.error('Erreur logout:', error);
        }
    }

    // Chat Handlers
    async function handleMessage(e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        const selectedModel = modelSelect.value;

        if (!message || !selectedModel) return;

        // Désactiver l'interface pendant l'envoi
        setFormState(true);

        // Ajouter le message utilisateur
        addMessage(message, true);

        // Réinitialiser l'input
        messageInput.value = '';
        updateCharCounter();
        adjustTextareaHeight();

        // Afficher l'indicateur de chargement
        const loadingIndicator = loadingTemplate.content.cloneNode(true);
        messagesContainer.appendChild(loadingIndicator);
        scrollToBottom();

        if (socket && socket.connected) {
            // Utiliser WebSocket pour le streaming
            socket.emit('chat_message', {
                model: selectedModel,
                messages: [{ role: 'user', content: message }]
            });
        } else {
            // Fallback sur HTTP si WebSocket n'est pas disponible
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: selectedModel,
                        messages: [{ role: 'user', content: message }]
                    })
                });

                const loadingElement = messagesContainer.querySelector('.loading')?.parentElement;
                if (loadingElement) {
                    loadingElement.remove();
                }

                if (!response.ok) throw new Error('Erreur réseau');

                const data = await response.json();
                addMessage(data.message.content, false);

            } catch (error) {
                console.error('Erreur:', error);
                addMessage("Une erreur s'est produite", false);
            } finally {
                setFormState(false);
            }
        }
    }

    function handleInput() {
        updateCharCounter();
        adjustTextareaHeight();
        sendButton.disabled = !messageInput.value.trim() || !modelSelect.value;
    }

    function handleModelSelect() {
        sendButton.disabled = !messageInput.value.trim() || !modelSelect.value;
        if (modelSelect.value) {
            document.querySelector('.welcome-message')?.remove();
        }
    }

    // Utility Functions
    async function loadModels() {
        try {
            const response = await fetch('/api/models');
            const models = await response.json();

            modelSelect.innerHTML = `
                <option value="" disabled selected>Sélectionner un modèle</option>
                ${models.map(model => `
                    <option value="${model.name}">${model.name} (${model.size})</option>
                `).join('')}
            `;
        } catch (error) {
            console.error('Erreur chargement modèles:', error);
            addMessage("Impossible de charger les modèles", false);
        }
    }

    function addMessage(content, isUser) {
        const messageElement = messageTemplate.content.cloneNode(true);
        const messageDiv = messageElement.querySelector('.message');
        const contentDiv = messageElement.querySelector('.message-content');
        const timeDiv = messageElement.querySelector('.message-time');

        messageDiv.classList.add(isUser ? 'user' : 'assistant');
        contentDiv.textContent = content;
        timeDiv.textContent = new Date().toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }

    function appendAssistantMessage(content) {
        const lastMessage = messagesContainer.querySelector('.message.assistant:last-child');

        if (lastMessage) {
            const contentDiv = lastMessage.querySelector('.message-content');
            contentDiv.textContent += content;
        } else {
            addMessage(content, false);
        }
        scrollToBottom();
    }

    function setFormState(disabled) {
        messageInput.disabled = disabled;
        sendButton.disabled = disabled;
        modelSelect.disabled = disabled;
    }

    function updateCharCounter() {
        const remaining = maxLength - messageInput.value.length;
        charCounter.textContent = remaining;
        charCounter.style.color = remaining < 100 ? 'var(--error-color)' : '';
    }

    function adjustTextareaHeight() {
        messageInput.style.height = 'auto';
        messageInput.style.height = `${Math.min(messageInput.scrollHeight, 200)}px`;
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});
