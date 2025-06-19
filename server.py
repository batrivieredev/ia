from flask import Flask, request, jsonify, session, send_from_directory
from functools import wraps
from db.database import db
import subprocess
import json

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète_ici'  # À changer en production

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Non autorisé'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' not in session or not session['is_admin']:
            return jsonify({'error': 'Accès refusé'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = db.verify_user(data['username'], data['password'])
    if user:
        session['user_id'] = user[0]
        session['is_admin'] = user[1]
        return jsonify({'success': True, 'is_admin': user[1]})
    return jsonify({'error': 'Identifiants invalides'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

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
        return response.stdout, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes d'administration
@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    users = db.get_users()
    return jsonify([{
        'id': user[0],
        'username': user[1],
        'is_admin': user[2],
        'created_at': user[3]
    } for user in users])

@app.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    data = request.json
    success = db.create_user(
        data['username'],
        data['password'],
        data.get('is_admin', False)
    )
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Nom d\'utilisateur déjà utilisé'}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.json
    success = db.update_user(
        user_id,
        data['username'],
        data.get('password', ''),
        data.get('is_admin', False)
    )
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Utilisateur non trouvé ou nom d\'utilisateur déjà utilisé'}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    success = db.delete_user(user_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Impossible de supprimer cet utilisateur'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
