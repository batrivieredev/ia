from flask import Flask, request, jsonify, session, send_from_directory
from functools import wraps
from db.database import db
import requests
import json
import os
from cachetools import TTLCache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'votre_clé_secrète_ici')

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

# Routes des préférences
@app.route('/api/preferences', methods=['GET'])
@login_required
def get_preferences():
    try:
        user_id = session['user_id']
        preferences = db.get_user_preferences(user_id)
        return jsonify(preferences)
    except Exception as e:
        app.logger.error(f'Erreur get_preferences: {str(e)}')
        return jsonify({'error': 'Erreur lors de la récupération des préférences'}), 500

@app.route('/api/preferences', methods=['POST'])
@login_required
def update_preferences():
    try:
        user_id = session['user_id']
        preferences = request.json
        success = db.update_preferences(user_id, preferences)

        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 400
    except Exception as e:
        app.logger.error(f'Erreur update_preferences: {str(e)}')
        return jsonify({'error': 'Erreur lors de la mise à jour des préférences'}), 500

# Routes du chat
@app.route('/api/models', methods=['GET'])
@login_required
def get_models():
    try:
        # Vérifier le cache
        if 'models' in models_cache:
            return jsonify(models_cache['models'])

        response = requests.get('http://localhost:11434/api/tags', timeout=5)

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
    except requests.Timeout:
        return jsonify({'error': 'Temps de réponse dépassé'}), 504
    except Exception as e:
        app.logger.error(f'Erreur get_models: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Route d'inscription publique
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Identifiants requis'}), 400

        success = db.create_user(
            username=username,
            password=password,
            is_admin=False
        )

        if success:
            user = db.verify_user(username, password)
            if user:
                session['user_id'] = user[0]
                session['is_admin'] = user[1]
                return jsonify({'success': True})

        return jsonify({'error': 'Nom d\'utilisateur déjà pris'}), 400
    except Exception as e:
        app.logger.error(f'Erreur register: {str(e)}')
        return jsonify({'error': 'Erreur d\'inscription'}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.json
        user_id = session['user_id']

        # Get user preferences
        user_prefs = db.get_user_preferences(user_id)

        # Construct system message
        system_msg = user_prefs.get('system_message', '')
        if user_prefs.get('interests'):
            system_msg += f"\nCentres d'intérêt de l'utilisateur: {', '.join(user_prefs['interests'])}"

        # Prepare messages with context
        messages = [
            {"role": "system", "content": system_msg},
            *data['messages']
        ]

        response = requests.post(
            f"http://{os.getenv('OLLAMA_HOST', 'localhost')}:{os.getenv('OLLAMA_PORT', '11434')}/api/chat",
            json={
                'model': data.get('model', user_prefs.get('model', 'phi')),
                'messages': messages,
                'stream': False
            },
            timeout=int(os.getenv('OLLAMA_TIMEOUT', '30'))
        )

        if response.status_code != 200:
            raise Exception('Erreur API Ollama')

        return jsonify(response.json()), 200
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
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        threaded=True
    )
