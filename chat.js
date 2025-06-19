document.addEventListener('DOMContentLoaded', () => {
    // Vérification de l'authentification
    checkAuth();

    // Éléments du DOM
    const modelSelect = document.getElementById('model-select');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatForm = document.getElementById('chat-form');
    const messagesContainer = document.getElementById('chat-messages');
    const logoutButton = document.getElementById('logout-button');
    const charCounter = document.querySelector('.char-counter');
    const maxLength = parseInt(messageInput.getAttribute('maxlength')) || 2000;

    // Templates
    const messageTemplate = document.getElementById('message-template');
    const loadingTemplate = document.getElementById('loading-template');

    // Chargement des modèles
    loadModels();

    // Event Listeners
    chatForm.addEventListener('submit', handleSubmit);
    logoutButton.addEventListener('click', handleLogout);
    messageInput.addEventListener('input', handleInput);
    modelSelect.addEventListener('change', handleModelSelect);

    // Gestion de l'authentification
    async function checkAuth() {
        try {
            const response = await fetch('/api/check-auth');
            if (!response.ok) {
                window.location.href = '/login.html';
            }
        } catch (error) {
            console.error('Erreur d\'authentification:', error);
            window.location.href = '/login.html';
        }
    }

    // Chargement des modèles disponibles
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
            showError('Impossible de charger les modèles');
        }
    }

    // Gestion des messages
    async function handleSubmit(e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        const selectedModel = modelSelect.value;

        if (!message || !selectedModel) return;

        // Désactiver l'interface pendant l'envoi
        setFormState(true);

        // Afficher le message utilisateur
        addMessage(message, true);

        // Réinitialiser l'input
        messageInput.value = '';
        updateCharCounter();
        adjustTextareaHeight();

        // Afficher l'indicateur de chargement
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

            // Supprimer l'indicateur de chargement
            const loadingElement = messagesContainer.querySelector('.loading').parentElement;
            loadingElement.remove();

            if (!response.ok) throw new Error('Erreur réseau');

            const data = await response.json();
            addMessage(data.message.content, false);

        } catch (error) {
            console.error('Erreur:', error);
            showError('Erreur lors de l\'envoi du message');
        } finally {
            setFormState(false);
        }
    }

    // Gestion de la déconnexion
    async function handleLogout() {
        try {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login.html';
        } catch (error) {
            console.error('Erreur de déconnexion:', error);
        }
    }

    // Fonctions utilitaires
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

    function showError(message) {
        addMessage(`Erreur: ${message}`, false);
    }

    function setFormState(disabled) {
        messageInput.disabled = disabled;
        sendButton.disabled = disabled;
        modelSelect.disabled = disabled;
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

    // Initialisation
    updateCharCounter();
    messageInput.focus();
});
