#!/usr/bin/env python3

import os
import logging
from logging.handlers import RotatingFileHandler
import subprocess
from flask import Flask
from server import app
from db.database import db

def check_requirements():
    """Vérifie les dépendances nécessaires"""
    try:
        # Vérifier PostgreSQL
        import psycopg2
    except ImportError:
        print("Erreur: psycopg2 n'est pas installé. Installez-le avec:")
        print("apt install python3-psycopg2")
        return False

    try:
        # Vérifier Flask
        import flask
    except ImportError:
        print("Erreur: Flask n'est pas installé. Installez-le avec:")
        print("apt install python3-flask")
        return False

    # Vérifier Ollama
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception()
    except:
        print("Erreur: Ollama n'est pas installé ou n'est pas en cours d'exécution.")
        print("Installez-le et démarrez-le avant de lancer l'application.")
        return False

    return True

def setup_logging():
    """Configure les logs de l'application"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application démarrée')

def init_app():
    """Initialise l'application"""
    # Configuration de production
    app.config.update(
        ENV='production',
        DEBUG=False,
        SECRET_KEY='changez_cette_cle_en_production',
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax'
    )

    # Initialisation de la base de données
    try:
        db.init_db()
        app.logger.info('Base de données initialisée')
    except Exception as e:
        app.logger.error(f'Erreur d\'initialisation de la base de données: {str(e)}')
        return False

    return True

if __name__ == '__main__':
    print("Démarrage de l'application...")

    # Vérifier les prérequis
    if not check_requirements():
        exit(1)

    # Configuration des logs
    setup_logging()

    # Initialisation de l'application
    if not init_app():
        print("Erreur lors de l'initialisation de l'application")
        exit(1)

    print("Application prête !")
    print("Accédez à l'interface sur: https://ia.fusikabdj.fr")
    print("Utilisateur par défaut: admin/admin")

    # Démarrage du serveur
    app.run(
        host='127.0.0.1',
        port=5000,
        threaded=True,
        debug=False
    )
