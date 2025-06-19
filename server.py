from flask import Flask, request, jsonify, session, send_from_directory
from functools import wraps
from db.database import db
import requests
import redis
import json
import os
from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète_ici'  # À changer en production

# Initialiser Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
CACHE_TTL = 3600  # 1 heure

# Thread pool pour les requêtes asynchrones
executor = ThreadPoolExecutor(max_workers=10)

# Cache pour les modèles (validité 1 heure)
models_cache = TTLCache(maxsize=100, ttl=3600)

# Timeouts
REQUEST_TIMEOUT = 5  # 5 secondes pour les requêtes normales
CHAT_TIMEOUT = 30   # 30 secondes pour les requêtes de chat

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
        # Vérifier le cache Redis
        cached_models = redis_client.get('models:list')
        if cached_models:
            return jsonify(json.loads(cached_models))

        # Faire la requête à Ollama avec timeout
        response = requests.get(
            'http://localhost:11434/api/tags',
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            raise Exception('Erreur Ollama list')

        models = []
        for model in response.json()['models']:
            name = model['name'].replace(':latest', '')
            models.append({
                'name': name,
                'size': f"{model['size']/(1024*1024*1024):.1f} GB"
            })

        # Mettre en cache Redis
        redis_client.setex('models:list', CACHE_TTL, json.dumps(models))
        return jsonify(models)
    except requests.Timeout:
        return jsonify({'error': 'Temps de réponse dépassé'}), 504
    except Exception as e:
        app.logger.error(f'Erreur get_models: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.json
        cache_key = f"chat:{data['model']}:{hash(str(data['messages']))}"

        # Vérifier le cache Redis
        cached_response = redis_client.get(cache_key)
        if cached_response:
            return jsonify(json.loads(cached_response)), 200

        response = requests.post(
            'http://localhost:11434/api/chat',
            json={
                'model': data['model'],
                'messages': data['messages'],
                'stream': False
            },
            timeout=CHAT_TIMEOUT
        )

        if response.status_code != 200:
            raise Exception('Erreur API Ollama')

        result = response.json()

        # Mettre en cache Redis
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
        return jsonify(result), 200
    except requests.Timeout:
        return jsonify({'error': 'Temps de réponse dépassé'}), 504
    except Exception as e:
        app.logger.error(f'Erreur chat: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Routes des utilisateurs
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
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Données manquantes'}), 400

    success = db.create_user(
        data['username'],
        data['password'],
        data.get('is_admin', False)
    )

    if success:
        redis_client.delete('users:list')  # Invalider le cache
        return jsonify({'success': True})
    return jsonify({'error': 'Nom d\'utilisateur déjà pris'}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Accès non autorisé'}), 403

    data = request.json
    if not data.get('username'):
        return jsonify({'error': 'Nom d\'utilisateur requis'}), 400

    success = db.update_user(
        user_id,
        data['username'],
        data.get('password'),
        data.get('is_admin', False)
    )

    if success:
        redis_client.delete('users:list')  # Invalider le cache
        return jsonify({'success': True})
    return jsonify({'error': 'Erreur lors de la mise à jour'}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Accès non autorisé'}), 403

    success = db.delete_user(user_id)
    if success:
        redis_client.delete('users:list')  # Invalider le cache
        return jsonify({'success': True})
    return jsonify({'error': 'Erreur lors de la suppression'}), 400

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Run in production mode
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        threaded=True
    )
