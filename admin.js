document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const userModal = document.getElementById('user-modal');
    const userForm = document.getElementById('user-form');
    const addUserBtn = document.getElementById('add-user-btn');
    const searchInput = document.getElementById('search-users');
    const logoutButton = document.getElementById('logout-button');
    const usersTableBody = document.getElementById('users-table-body');
    const modalTitle = document.getElementById('modal-title');

    // Bootstrap Modal
    const modal = new bootstrap.Modal(userModal);
    const closeBtn = userModal.querySelector('.btn-close');
    const cancelBtn = userModal.querySelector('.btn-outline-secondary');

    // Event Listeners
    addUserBtn.addEventListener('click', openModal);
    userForm.addEventListener('submit', handleUserSubmit);
    searchInput.addEventListener('input', handleSearch);
    logoutButton.addEventListener('click', handleLogout);
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // Variables
    let editingUserId = null;
    let users = [];

    // Check auth and load users
    checkAdminAuth();

    async function checkAdminAuth() {
        try {
            const response = await fetch('/api/auth/check');
            const data = await response.json();

            if (!data.authenticated || !data.is_admin) {
                window.location.href = '/login.html';
            } else {
                await loadUsers();
            }
        } catch (error) {
            console.error('Erreur auth:', error);
            window.location.href = '/login.html';
        }
    }

    async function loadUsers() {
        try {
            const response = await fetch('/api/users');
            if (!response.ok) {
                throw new Error('Erreur lors du chargement des utilisateurs');
            }
            users = await response.json();
            renderUsers(users);
        } catch (error) {
            console.error('Erreur:', error);
            alert(error.message);
        }
    }

    function renderUsers(usersToRender) {
        usersTableBody.innerHTML = usersToRender.map(user => `
            <tr>
                <td>${escapeHtml(user.username)}</td>
                <td>${formatDate(user.created_at)}</td>
                <td>
                    <span class="badge ${user.is_admin ? 'badge-success' : 'badge-secondary'}">
                        ${user.is_admin ? 'Oui' : 'Non'}
                    </span>
                </td>
                <td>
                    <div class="user-actions">
                        <button onclick="editUser(${user.id})" class="btn btn-outline-primary btn-sm">
                            <i class="bi bi-pencil"></i> Modifier
                        </button>
                        ${user.username !== 'admin' ?
                            `<button onclick="deleteUser(${user.id})" class="btn btn-danger btn-sm">
                                <i class="bi bi-trash"></i> Supprimer
                            </button>`
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
            username: document.getElementById('username').value.trim(),
            password: document.getElementById('password').value,
            is_admin: document.getElementById('is-admin').checked
        };

        if (!formData.username) {
            alert("Le nom d'utilisateur est requis");
            return;
        }

        if (!editingUserId && !formData.password) {
            alert("Le mot de passe est requis pour un nouvel utilisateur");
            return;
        }

        try {
            const url = editingUserId ? `/api/users/${editingUserId}` : '/api/users';
            const method = editingUserId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Une erreur s'est produite");
            }

            await loadUsers();
            closeModal();
        } catch (error) {
            console.error('Erreur:', error);
            alert(error.message);
        }
    }

    window.editUser = async (userId) => {
        editingUserId = userId;
        const user = users.find(u => u.id === userId);

        if (user) {
            modalTitle.textContent = "Modifier l'utilisateur";
            document.getElementById('username').value = user.username;
            document.getElementById('password').value = '';
            document.getElementById('is-admin').checked = user.is_admin;
            modal.show();
        }
    };

    window.deleteUser = async (userId) => {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) return;

        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Erreur lors de la suppression');
            }

            await loadUsers();
        } catch (error) {
            console.error('Erreur:', error);
            alert(error.message);
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
        editingUserId = null;
        modalTitle.textContent = 'Nouvel utilisateur';
        userForm.reset();
        modal.show();
    }

    function closeModal() {
        modal.hide();
        userForm.reset();
        editingUserId = null;
    }

    // Utility functions
    function formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
