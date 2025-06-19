#!/usr/bin/env python3

from server import app
import os
import logging
from logging.handlers import RotatingFileHandler

# Configuration des logs
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configuration du logging
formatter = logging.Formatter(
    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application démarrée')

if __name__ == '__main__':
    # Configuration de production
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False

    # Démarrage du serveur
    app.run(
        host='127.0.0.1',      # Écoute uniquement sur localhost
        port=5000,             # Port par défaut
        threaded=True,         # Support multi-thread
        debug=False            # Mode production
    )
