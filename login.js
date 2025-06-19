document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const formError = document.querySelector('.form-error');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const submitButton = loginForm.querySelector('button[type="submit"]');

        // Désactiver le bouton pendant la requête
        submitButton.disabled = true;
        formError.classList.add('hidden');

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                // Animation de transition
                document.body.style.opacity = '0';
                setTimeout(() => {
                    window.location.href = '/chat.html';
                }, 300);
            } else {
                formError.classList.remove('hidden');
                submitButton.disabled = false;

                // Animation du champ en erreur
                const inputs = loginForm.querySelectorAll('input');
                inputs.forEach(input => {
                    input.style.borderColor = 'var(--error-color)';
                    setTimeout(() => {
                        input.style.borderColor = '';
                    }, 2000);
                });
            }
        } catch (error) {
            console.error('Erreur:', error);
            formError.textContent = 'Erreur de connexion au serveur';
            formError.classList.remove('hidden');
            submitButton.disabled = false;
        }
    });

    // Réinitialiser les erreurs lors de la saisie
    const inputs = loginForm.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            formError.classList.add('hidden');
            input.style.borderColor = '';
        });
    });

    // Focus automatique sur le premier champ
    document.getElementById('username').focus();

    // Transition d'entrée
    document.body.style.opacity = '0';
    requestAnimationFrame(() => {
        document.body.style.transition = 'opacity 0.3s ease-in';
        document.body.style.opacity = '1';
    });
});
