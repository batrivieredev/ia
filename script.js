document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const loginContainer = document.getElementById('login-container');
    const chatContainer = document.getElementById('chat-container');
    const loginForm = document.getElementById('login-form');
    const chatForm = document.getElementById('chat-form');
    const logoutButton = document.getElementById('logout-button');
    const modelSelect = document.getElementById('model-select');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('chat-messages');
    const formError = document.querySelector('.form-error');
    const charCounter = document.querySelector('.char-counter');
    const maxLength = parseInt(messageInput.getAttribute('maxlength')) || 2000;

    // Templates
    const messageTemplate = document.getElementById('message-template');
    const loadingTemplate = document.getElementById('loading-template');

    // Event Listeners
    loginForm.addEventListener('submit', handleLogin);
    chatForm.addEventListener('submit', handleMessage);
    logoutButton.addEventListener('click', handleLogout);
    messageInput.addEventListener('input', handleInput);
    modelSelect.addEventListener('change', handleModelSelect);

    // Auth Handlers
    async function handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const submitButton = loginForm.querySelector('button[type="submit"]');

        submitButton.disabled = true;
        formError.classList.add('hidden');

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                showChat();
                loadModels();
                loginForm.reset();
            } else {
                formError.classList.remove('hidden');
                loginForm.querySelector('input[type="password"]').value = '';
            }
        } catch (error) {
            console.error('Erreur:', error);
            formError.textContent = 'Erreur de connexion';
            formError.classList.remove('hidden');
        } finally {
            submitButton.disabled = false;
        }
    }

    async function handleLogout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            showLogin();
        } catch (error) {
            console.error('Erreur de déconnexion:', error);
        }
    }

    // Chat Handlers
    async function handleMessage(e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        const selectedModel = modelSelect.value;

        if (!message || !selectedModel) return;

        // Disable interface while sending
        setFormState(true);

        // Add user message
        addMessage(message, true);

        // Reset input
        messageInput.value = '';
        updateCharCounter();
        adjustTextareaHeight();

        // Show loading indicator
        const loadingIndicator = loadingTemplate.content.cloneNode(true);
        messagesContainer.appendChild(loadingIndicator);
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: selectedModel,
                    messages: [{ role: 'user', content: message }]
                })
            });

            // Remove loading indicator
            const loadingElement = messagesContainer.querySelector('.loading').parentElement;
            loadingElement.remove();

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

    // UI Handlers
    function showLogin() {
        loginContainer.classList.remove('hidden');
        chatContainer.classList.add('hidden');
        loginForm.reset();
        document.getElementById('username').focus();
    }

    function showChat() {
        loginContainer.classList.add('hidden');
        chatContainer.classList.remove('hidden');
        messageInput.focus();
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

    // Check auth status on load
    fetch('/api/auth/check')
        .then(response => response.json())
        .then(data => {
            if (data.authenticated) {
                showChat();
                loadModels();
            } else {
                showLogin();
            }
        })
        .catch(() => showLogin());
});
