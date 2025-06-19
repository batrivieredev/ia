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

def install_package(package):
    """Installe un paquet via apt"""
    print(f"Installation de {package}...")
    try:
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

    requirements = {
        'python3-flask': 'Flask',
        'python3-psycopg2': 'psycopg2',
        'postgresql': 'PostgreSQL',
        'curl': 'curl'
    }

    missing_packages = []

    # Vérifier Python packages
    try:
        import flask
        print("✓ Flask est installé")
    except ImportError:
        missing_packages.append('python3-flask')

    try:
        import psycopg2
        print("✓ psycopg2 est installé")
    except ImportError:
        missing_packages.append('python3-psycopg2')

    # Vérifier PostgreSQL
    if not check_command('psql'):
        missing_packages.append('postgresql')
    else:
        print("✓ PostgreSQL est installé")

    # Vérifier curl
    if not check_command('curl'):
        missing_packages.append('curl')
    else:
        print("✓ curl est installé")

    # Vérifier Ollama
    print("\nVérification d'Ollama...")
    if not check_command('ollama'):
        print("✗ Ollama n'est pas installé")
        print("Pour installer Ollama, suivez les instructions sur: https://ollama.ai/download")
        return False
    else:
        print("✓ Ollama est installé")

    # Installer les paquets manquants
    if missing_packages:
        print("\nInstallation des paquets manquants...")
        for package in missing_packages:
            if not install_package(package):
                return False

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
