from flask import Flask, request, jsonify, session, send_from_directory
from functools import wraps
from db.database import db
import requests
import json
import os
from cachetools import TTLCache

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète_ici'  # À changer en production

# Cache pour les modèles (validité 1 heure)
models_cache = TTLCache(maxsize=100, ttl=3600)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Non autorisé', 'authenticated': False}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# Routes d'authentification
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Identifiants manquants'}), 400

        user = db.verify_user(username, password)

        if user:
            session['user_id'] = user[0]
            session['is_admin'] = user[1]
            return jsonify({
                'success': True,
                'authenticated': True,
                'is_admin': user[1]
            })

        return jsonify({'error': 'Identifiants invalides'}), 401
    except Exception as e:
        app.logger.error(f'Erreur de login: {str(e)}')
        return jsonify({'error': 'Erreur de connexion'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/check')
def check_auth():
    is_authenticated = 'user_id' in session
    return jsonify({
        'authenticated': is_authenticated,
        'is_admin': session.get('is_admin', False) if is_authenticated else False
    })

# Routes du chat
@app.route('/api/models', methods=['GET'])
@login_required
def get_models():
    try:
        # Vérifier le cache
        if 'models' in models_cache:
            return jsonify(models_cache['models'])

        # Faire la requête à Ollama
        response = requests.get('http://localhost:11434/api/tags')

        if response.status_code != 200:
            raise Exception('Erreur Ollama list')

        models = []
        for model in response.json()['models']:
            name = model['name'].replace(':latest', '')
            models.append({
                'name': name,
                'size': f"{model['size']/(1024*1024*1024):.1f} GB"
            })

        # Mettre en cache
        models_cache['models'] = models
        return jsonify(models)
    except Exception as e:
        app.logger.error(f'Erreur get_models: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.json
        response = requests.post(
            'http://localhost:11434/api/chat',
            json={
                'model': data['model'],
                'messages': data['messages'],
                'stream': False
            }
        )

        if response.status_code != 200:
            raise Exception('Erreur API Ollama')

        return jsonify(response.json()), 200
    except Exception as e:
        app.logger.error(f'Erreur chat: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if not session.get('is_admin'):
        return jsonify({'error': 'Accès non autorisé'}), 403
    return jsonify(db.get_users())

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if not session.get('is_admin'):
        return jsonify({'error': 'Accès non autorisé'}), 403

    data = request.json
    success = db.create_user(
        data['username'],
        data['password'],
        data.get('is_admin', False)
    )

    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Nom d\'utilisateur déjà pris'}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Accès non autorisé'}), 403

    data = request.json
    success = db.update_user(
        user_id,
        data['username'],
        data.get('password'),
        data.get('is_admin', False)
    )

    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Erreur lors de la mise à jour'}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Accès non autorisé'}), 403

    success = db.delete_user(user_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Erreur lors de la suppression'}), 400

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Run in production mode
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False
    )
