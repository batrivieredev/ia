#!/usr/bin/env python3

import subprocess
import sys
import os

def check_command(command):
    """Vérifie si une commande est disponible"""
    try:
        subprocess.run([command, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def install_package(package, use_pip=False):
    """Installe un paquet via apt ou pip"""
    print(f"Installation de {package}...")
    try:
        if use_pip:
            subprocess.run(['pip3', 'install', '--break-system-packages', package], check=True)
        else:
            subprocess.run(['apt', 'install', '-y', package], check=True)
        print(f"✓ {package} installé")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Erreur lors de l'installation de {package}")
        return False

def check_and_install_requirements():
    """Vérifie et installe les dépendances nécessaires"""

    if os.geteuid() != 0:
        print("Ce script doit être exécuté en tant que root")
        return False

    print("Vérification des dépendances...")

    # Vérifier/installer pip si nécessaire
    if not check_command('pip3'):
        if not install_package('python3-pip'):
            return False
    print("✓ pip3 est installé")

    # Installer Flask et psycopg2 via pip
    try:
        import flask
        print("✓ Flask est installé")
    except ImportError:
        if not install_package('flask', use_pip=True):
            return False

    try:
        import psycopg2
        print("✓ psycopg2 est installé")
    except ImportError:
        # Installer les dépendances de compilation pour psycopg2
        install_package('python3-dev')
        install_package('libpq-dev')
        if not install_package('psycopg2-binary', use_pip=True):
            return False

    # Vérifier PostgreSQL
    if not check_command('psql'):
        if not install_package('postgresql'):
            return False
    print("✓ PostgreSQL est installé")

    # Vérifier curl
    if not check_command('curl'):
        if not install_package('curl'):
            return False
    print("✓ curl est installé")

    # Vérifier Ollama
    print("\nVérification d'Ollama...")
    if not check_command('ollama'):
        print("✗ Ollama n'est pas installé")
        print("Pour installer Ollama, suivez les instructions sur: https://ollama.ai/download")
        return False
    print("✓ Ollama est installé")

    # Vérifier que PostgreSQL est démarré
    print("\nVérification du service PostgreSQL...")
    try:
        subprocess.run(['systemctl', 'is-active', '--quiet', 'postgresql'])
        print("✓ PostgreSQL est en cours d'exécution")
    except subprocess.CalledProcessError:
        print("Démarrage de PostgreSQL...")
        try:
            subprocess.run(['systemctl', 'start', 'postgresql'], check=True)
            print("✓ PostgreSQL démarré")
        except subprocess.CalledProcessError:
            print("✗ Impossible de démarrer PostgreSQL")
            return False

    # Vérifier la base de données
    print("\nVérification de la base de données...")
    try:
        import db.database
        db.database.db.init_db()
        print("✓ Base de données initialisée")
    except Exception as e:
        print(f"✗ Erreur d'initialisation de la base de données: {str(e)}")
        return False

    print("\n✓ Toutes les dépendances sont installées et configurées !")
    return True

if __name__ == '__main__':
    print("=== Vérification des prérequis pour l'application IA Chat ===\n")
    if check_and_install_requirements():
        print("\nVous pouvez maintenant lancer l'application avec:")
        print("python3 run.py")
    else:
        print("\n✗ Erreur lors de la vérification des prérequis")
        sys.exit(1)
