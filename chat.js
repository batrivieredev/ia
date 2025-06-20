document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const chatForm = document.getElementById('chat-form');
    const logoutButton = document.getElementById('logout-button');
    const preferencesButton = document.getElementById('preferences-button');
    const modelSelect = document.getElementById('model-select');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('chat-messages');
    const charCounter = document.querySelector('.char-counter');
    const maxLength = parseInt(messageInput.getAttribute('maxlength')) || 2000;

    // Preferences elements
    const preferencesModal = new bootstrap.Modal('#preferences-modal');
    const defaultModelSelect = document.getElementById('default-model');
    const interestInput = document.getElementById('interest-input');
    const addInterestButton = document.getElementById('add-interest');
    const interestsList = document.getElementById('interests-list');
    const systemMessage = document.getElementById('system-message');
    const savePreferencesButton = document.getElementById('save-preferences');

    // Current preferences state
    let currentPreferences = {
        model: '',
        interests: [],
        system_message: ''
    };

    // Templates
    const messageTemplate = document.getElementById('message-template');
    const loadingTemplate = document.getElementById('loading-template');

    // Event Listeners
    chatForm.addEventListener('submit', handleMessage);
    logoutButton.addEventListener('click', handleLogout);
    messageInput.addEventListener('input', handleInput);
    modelSelect.addEventListener('change', handleModelSelect);
    preferencesButton.addEventListener('click', () => {
        loadUserPreferences();
        preferencesModal.show();
    });
    addInterestButton.addEventListener('click', addInterest);
    savePreferencesButton.addEventListener('click', savePreferences);

    // Vérifier l'authentification
    checkAuth();

    async function checkAuth() {
        try {
            const response = await fetch('/api/auth/check');
            const data = await response.json();

            if (!data.authenticated) {
                window.location.href = '/login.html';
            } else {
                await loadModels();
                await loadUserPreferences();
            }
        } catch (error) {
            console.error('Erreur auth:', error);
            window.location.href = '/login.html';
        }
    }

    async function handleLogout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
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

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: selectedModel,
                    messages: [{ role: 'user', content: message }],
                    preferences: currentPreferences
                })
            });

            // Supprimer l'indicateur de chargement
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

    // Preferences Functions
    async function loadUserPreferences() {
        try {
            const response = await fetch('/api/preferences');
            if (!response.ok) throw new Error('Erreur réseau');

            const prefs = await response.json();
            currentPreferences = prefs;

            // Update modal fields
            defaultModelSelect.value = prefs.model || '';
            systemMessage.value = prefs.system_message || '';

            // Update interests list
            interestsList.innerHTML = '';
            prefs.interests.forEach(interest => {
                addInterestTag(interest);
            });

            // Update model select if needed
            if (prefs.model && !modelSelect.value) {
                modelSelect.value = prefs.model;
                handleModelSelect();
            }
        } catch (error) {
            console.error('Erreur chargement préférences:', error);
        }
    }

    async function savePreferences() {
        const preferences = {
            model: defaultModelSelect.value,
            interests: Array.from(interestsList.children).map(tag => tag.dataset.value),
            system_message: systemMessage.value
        };

        try {
            const response = await fetch('/api/preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preferences)
            });

            if (!response.ok) throw new Error('Erreur réseau');

            currentPreferences = preferences;
            preferencesModal.hide();

            // Update model if needed
            if (preferences.model && !modelSelect.value) {
                modelSelect.value = preferences.model;
                handleModelSelect();
            }
        } catch (error) {
            console.error('Erreur sauvegarde préférences:', error);
        }
    }

    function addInterest() {
        const interest = interestInput.value.trim();
        if (!interest) return;

        addInterestTag(interest);
        interestInput.value = '';
    }

    function addInterestTag(interest) {
        const tag = document.createElement('span');
        tag.className = 'badge bg-primary me-2 mb-2';
        tag.dataset.value = interest;
        tag.innerHTML = `
            ${interest}
            <button type="button" class="btn-close btn-close-white ms-2" onclick="this.parentElement.remove()"></button>
        `;
        interestsList.appendChild(tag);
    }

    // Utility Functions
    async function loadModels() {
        try {
            const response = await fetch('/api/models');
            const models = await response.json();

            const modelsHtml = models.map(model => `
                <option value="${model.name}">${model.name} (${model.size})</option>
            `).join('');

            // Update both selects
            modelSelect.innerHTML = `
                <option value="" disabled selected>Sélectionner un modèle</option>
                ${modelsHtml}
            `;
            defaultModelSelect.innerHTML = `
                <option value="">Aucun modèle par défaut</option>
                ${modelsHtml}
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
});
