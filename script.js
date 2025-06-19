document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const loginContainer = document.getElementById('login-container');
    const adminContainer = document.getElementById('admin-container');
    const chatContainer = document.getElementById('chat-container');
    const loginForm = document.getElementById('login-form');
    const adminButton = document.getElementById('admin-button');
    const returnToChatButton = document.getElementById('return-to-chat');
    const logoutButtons = document.querySelectorAll('#logout-button, #chat-logout-button');
    const usersList = document.getElementById('users-list');
    const addUserButton = document.getElementById('add-user-button');
    const userModal = document.getElementById('user-modal');
    const userForm = document.getElementById('user-form');
    const modalCancel = document.getElementById('modal-cancel');
    const modelSelect = document.getElementById('model-select');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    let currentUserId = null;
    let isAdmin = false;

    // Auth Management
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();

            if (data.success) {
                isAdmin = data.is_admin;
                showChat();
                if (isAdmin) {
                    adminButton.classList.remove('hidden');
                }
                loadModels();
            } else {
                alert('Identifiants invalides');
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur de connexion');
        }
    });

    logoutButtons.forEach(button => {
        button.addEventListener('click', async () => {
            await fetch('/api/logout', { method: 'POST' });
            showLogin();
        });
    });

    // Navigation
    function showLogin() {
        loginContainer.classList.remove('hidden');
        adminContainer.classList.add('hidden');
        chatContainer.classList.add('hidden');
        adminButton.classList.add('hidden');
        isAdmin = false;
        currentUserId = null;
    }

    function showAdmin() {
        loginContainer.classList.add('hidden');
        adminContainer.classList.remove('hidden');
        chatContainer.classList.add('hidden');
        loadUsers();
    }

    function showChat() {
        loginContainer.classList.add('hidden');
        adminContainer.classList.add('hidden');
        chatContainer.classList.remove('hidden');
    }

    adminButton.addEventListener('click', showAdmin);
    returnToChatButton.addEventListener('click', showChat);

    // Models Management
    async function loadModels() {
        try {
            const response = await fetch('/api/models');
            const models = await response.json();
            modelSelect.innerHTML = '<option value="">Sélectionner un modèle</option>' +
                models.map(model => `
                    <option value="${model.name}">${model.name} (${model.size})</option>
                `).join('');
        } catch (error) {
            console.error('Erreur chargement modèles:', error);
        }
    }

    // Chat Management
    let chatHistory = [];

    async function sendMessage() {
        const message = userInput.value.trim();
        const selectedModel = modelSelect.value;

        if (!message || !selectedModel) return;

        addMessage(message, true);
        userInput.value = '';
        userInput.style.height = 'auto';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: selectedModel,
                    messages: [{ role: 'user', content: message }]
                })
            });

            if (!response.ok) throw new Error('Erreur réseau');

            const data = await response.json();
            addMessage(data.message.content, false);
        } catch (error) {
            console.error('Erreur:', error);
            addMessage("Désolé, une erreur s'est produite", false);
        }
    }

    function addMessage(content, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
        messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        chatHistory.push({ role: isUser ? 'user' : 'assistant', content });
    }

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Users Management
    async function loadUsers() {
        try {
            const response = await fetch('/api/users');
            const users = await response.json();
            usersList.innerHTML = users.map(user => `
                <div class="user-item">
                    <div class="user-info">
                        <span class="username">${user.username}</span>
                        <span class="created-at">Créé le ${new Date(user.created_at).toLocaleDateString()}</span>
                    </div>
                    <div class="user-actions">
                        <button onclick="editUser(${user.id})" class="secondary-button">Modifier</button>
                        <button onclick="deleteUser(${user.id})" class="secondary-button">Supprimer</button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Erreur chargement utilisateurs:', error);
        }
    }

    async function saveUser(e) {
        e.preventDefault();
        const username = document.getElementById('modal-username').value;
        const password = document.getElementById('modal-password').value;
        const isAdmin = document.getElementById('modal-is-admin').checked;

        const userData = { username, password, is_admin: isAdmin };
        const url = currentUserId ?
            `/api/users/${currentUserId}` : '/api/users';
        const method = currentUserId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                closeModal();
                loadUsers();
            } else {
                const error = await response.json();
                alert(error.error);
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la sauvegarde');
        }
    }

    window.editUser = async (userId) => {
        currentUserId = userId;
        const response = await fetch(`/api/users/${userId}`);
        const user = await response.json();

        document.getElementById('modal-username').value = user.username;
        document.getElementById('modal-password').value = '';
        document.getElementById('modal-is-admin').checked = user.is_admin;

        document.getElementById('modal-title').textContent = 'Modifier l\'utilisateur';
        userModal.classList.remove('hidden');
    };

    window.deleteUser = async (userId) => {
        if (!confirm('Voulez-vous vraiment supprimer cet utilisateur ?')) return;

        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                loadUsers();
            } else {
                const error = await response.json();
                alert(error.error);
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la suppression');
        }
    };

    function closeModal() {
        userModal.classList.add('hidden');
        userForm.reset();
        currentUserId = null;
    }

    addUserButton.addEventListener('click', () => {
        document.getElementById('modal-title').textContent = 'Ajouter un utilisateur';
        userModal.classList.remove('hidden');
    });

    modalCancel.addEventListener('click', closeModal);
    userForm.addEventListener('submit', saveUser);

    // Textarea auto-resize
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Initial state
    showLogin();
});
