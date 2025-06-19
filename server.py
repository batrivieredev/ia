from flask import Flask, request, jsonify, session, send_from_directory
from functools import wraps
from db.database import db
import subprocess
import json
import os

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète_ici'  # À changer en production

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
    data = request.json
    user = db.verify_user(data['username'], data['password'])
    if user:
        session['user_id'] = user[0]
        session['is_admin'] = user[1]
        return jsonify({'success': True, 'authenticated': True})
    return jsonify({'error': 'Identifiants invalides', 'authenticated': False}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/check')
def check_auth():
    return jsonify({
        'authenticated': 'user_id' in session,
        'is_admin': session.get('is_admin', False)
    })

# Routes du chat
@app.route('/api/models', methods=['GET'])
@login_required
def get_models():
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        models = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 5:
                name = parts[0].replace(':latest', '')
                models.append({
                    'name': name,
                    'id': parts[1],
                    'size': parts[2] + ' ' + parts[3]
                })
        return jsonify(models)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    try:
        response = subprocess.run([
            'curl', '-X', 'POST', 'http://localhost:11434/api/chat',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                'model': data['model'],
                'messages': data['messages'],
                'stream': False
            })
        ], capture_output=True, text=True)

        if response.returncode != 0:
            raise Exception('Erreur API Ollama')

        return response.stdout, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('logs', exist_ok=True)

    # Run in production mode
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False
    )
