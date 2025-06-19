document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const userModal = document.getElementById('user-modal');
    const userForm = document.getElementById('user-form');
    const addUserBtn = document.getElementById('add-user-btn');
    const closeBtn = document.querySelector('.close-button');
    const cancelBtn = document.getElementById('cancel-button');
    const searchInput = document.getElementById('search-users');
    const logoutButton = document.getElementById('logout-button');
    const usersTableBody = document.getElementById('users-table-body');

    // Event Listeners
    addUserBtn.addEventListener('click', () => openModal());
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    userForm.addEventListener('submit', handleUserSubmit);
    searchInput.addEventListener('input', debounce(handleSearch, 300));
    logoutButton.addEventListener('click', handleLogout);

    // Vérifier l'authentification admin
    checkAdminAuth();

    let editingUserId = null;
    let users = [];

    async function checkAdminAuth() {
        try {
            const response = await fetch('/api/auth/check');
            const data = await response.json();

            if (!data.authenticated || !data.is_admin) {
                window.location.href = '/login.html';
            } else {
                loadUsers();
            }
        } catch (error) {
            console.error('Erreur auth:', error);
            window.location.href = '/login.html';
        }
    }

    async function loadUsers() {
        try {
            const response = await fetch('/api/users');
            users = await response.json();
            renderUsers(users);
        } catch (error) {
            console.error('Erreur chargement utilisateurs:', error);
        }
    }

    function renderUsers(usersToRender) {
        usersTableBody.innerHTML = usersToRender.map(user => `
            <tr>
                <td>${user.username}</td>
                <td>${new Date(user.created_at).toLocaleDateString('fr-FR')}</td>
                <td>
                    <span class="${user.is_admin ? 'success-color' : 'text-secondary'}">
                        ${user.is_admin ? 'Oui' : 'Non'}
                    </span>
                </td>
                <td>
                    <div class="user-actions">
                        <button onclick="editUser(${user.id})" class="secondary-button">Modifier</button>
                        ${user.username !== 'admin' ?
                            `<button onclick="deleteUser(${user.id})" class="danger-button">Supprimer</button>`
                            : ''
                        }
                    </div>
                </td>
            </tr>
        `).join('');
    }

    async function handleUserSubmit(e) {
        e.preventDefault();

        const formData = {
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            is_admin: document.getElementById('is-admin').checked
        };

        try {
            const url = editingUserId ? `/api/users/${editingUserId}` : '/api/users';
            const method = editingUserId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) throw new Error('Erreur réseau');

            await loadUsers();
            closeModal();
        } catch (error) {
            console.error('Erreur:', error);
            alert("Une erreur s'est produite");
        }
    }

    window.editUser = async (userId) => {
        editingUserId = userId;
        const user = users.find(u => u.id === userId);

        if (user) {
            document.getElementById('modal-title').textContent = 'Modifier l\'utilisateur';
            document.getElementById('username').value = user.username;
            document.getElementById('password').value = '';
            document.getElementById('is-admin').checked = user.is_admin;
            document.querySelector('.password-notice').style.display = 'block';
            openModal();
        }
    };

    window.deleteUser = async (userId) => {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) return;

        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Erreur réseau');

            await loadUsers();
        } catch (error) {
            console.error('Erreur:', error);
            alert("Une erreur s'est produite");
        }
    };

    function handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();
        const filteredUsers = users.filter(user =>
            user.username.toLowerCase().includes(searchTerm)
        );
        renderUsers(filteredUsers);
    }

    async function handleLogout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            window.location.href = '/login.html';
        } catch (error) {
            console.error('Erreur logout:', error);
        }
    }

    function openModal() {
        if (!editingUserId) {
            document.getElementById('modal-title').textContent = 'Nouvel utilisateur';
            userForm.reset();
            document.querySelector('.password-notice').style.display = 'none';
        }
        userModal.classList.add('active');
    }

    function closeModal() {
        userModal.classList.remove('active');
        editingUserId = null;
        userForm.reset();
    }

    // Utility
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});
