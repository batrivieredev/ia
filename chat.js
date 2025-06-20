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
    const modalContent = document.querySelector('.modal-content');

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

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
    preferencesButton.addEventListener('click', showPreferences);
    addInterestButton.addEventListener('click', addInterest);
    savePreferencesButton.addEventListener('click', savePreferences);

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'p') {
            e.preventDefault();
            showPreferences();
        }
        if (e.key === 'Enter' && !e.shiftKey && document.activeElement === messageInput) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Add interest on Enter key
    interestInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addInterest();
        }
    });

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

    async function showPreferences() {
        modalContent.style.opacity = '0.5';
        preferencesModal.show();
        await loadUserPreferences();
        modalContent.style.opacity = '1';
        modalContent.style.transition = 'opacity 0.3s ease';
    }

    function showNotification(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
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
            showNotification('Préférences enregistrées avec succès');
            preferencesModal.hide();

            // Update model if needed
            if (preferences.model && !modelSelect.value) {
                modelSelect.value = preferences.model;
                handleModelSelect();
            }
        } catch (error) {
            console.error('Erreur sauvegarde préférences:', error);
            showNotification('Erreur lors de la sauvegarde des préférences', 'danger');
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
        tag.className = 'badge bg-primary me-2 mb-2 animate__animated animate__fadeInRight';
        tag.dataset.value = interest;
        tag.innerHTML = `
            <i class="bi bi-tag me-1"></i>
            ${interest}
            <button type="button" class="btn-close btn-close-white ms-2" onclick="removeInterest(this.parentElement)"></button>
        `;
        tag.style.opacity = '0';
        tag.style.transform = 'translateX(-10px)';
        interestsList.appendChild(tag);

        // Trigger animation
        setTimeout(() => {
            tag.style.transition = 'all 0.3s ease';
            tag.style.opacity = '1';
            tag.style.transform = 'translateX(0)';
        }, 50);
    }

    function removeInterest(tag) {
        tag.style.opacity = '0';
        tag.style.transform = 'translateX(-10px)';
        setTimeout(() => tag.remove(), 300);
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

        messageDiv.classList.add(isUser ? 'user' : 'fusikab');
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
        const target = messagesContainer.scrollHeight;
        messagesContainer.scrollTo({
            top: target,
            behavior: 'smooth'
        });
    }
});
