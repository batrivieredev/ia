#!/usr/bin/env python3

import subprocess
import sys
import os
import time

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

def setup_redis():
    """Configure et démarre Redis"""
    print("\nConfiguration de Redis...")

    # Installer Redis si nécessaire
    if not check_command('redis-server'):
        if not install_package('redis-server'):
            return False
    print("✓ Redis est installé")

    # Démarrer Redis
    print("Démarrage de Redis...")
    try:
        subprocess.run(['systemctl', 'start', 'redis-server'], check=True)
        time.sleep(2)
        print("✓ Redis démarré")
    except subprocess.CalledProcessError:
        print("✗ Impossible de démarrer Redis")
        return False

    # Activer Redis au démarrage
    try:
        subprocess.run(['systemctl', 'enable', 'redis-server'], check=True)
        print("✓ Redis activé au démarrage")
    except subprocess.CalledProcessError:
        print("! Note: Redis ne démarrera pas automatiquement au reboot")

    return True

def setup_mysql():
    """Configure et démarre MySQL"""
    print("\nConfiguration de MySQL...")

    # Installer MySQL si nécessaire
    if not check_command('mysql'):
        if not install_package('mysql-server'):
            return False
    print("✓ MySQL est installé")

    # Démarrer MySQL
    print("Démarrage de MySQL...")
    try:
        subprocess.run(['systemctl', 'start', 'mysql'], check=True)
        time.sleep(5)
        print("✓ MySQL démarré")
    except subprocess.CalledProcessError:
        print("✗ Impossible de démarrer MySQL")
        return False

    # Activer MySQL au démarrage
    try:
        subprocess.run(['systemctl', 'enable', 'mysql'], check=True)
        print("✓ MySQL activé au démarrage")
    except subprocess.CalledProcessError:
        print("! Note: MySQL ne démarrera pas automatiquement au reboot")

    # Créer l'utilisateur et la base de données
    try:
        commands = [
            "CREATE DATABASE IF NOT EXISTS ia_chat;",
            "CREATE USER IF NOT EXISTS 'ia_user'@'localhost' IDENTIFIED BY 'ia_password';",
            "GRANT ALL PRIVILEGES ON ia_chat.* TO 'ia_user'@'localhost';",
            "FLUSH PRIVILEGES;"
        ]

        for command in commands:
            subprocess.run([
                'mysql', '-u', 'root',
                '-e', command
            ], check=True)
        print("✓ Base de données et utilisateur créés")

        # Initialiser la base avec le schéma
        subprocess.run([
            'mysql', '-u', 'root',
            'ia_chat',
            '-e', f"source {os.path.join('db', 'init_mysql.sql')}"
        ], check=True)
        print("✓ Schéma de la base de données initialisé")
    except subprocess.CalledProcessError as e:
        print(f"✗ Erreur lors de la configuration de la base de données: {str(e)}")
        return False

    return True

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

    # Installer les dépendances de compilation
    build_deps = ['python3-dev', 'build-essential', 'libssl-dev', 'libffi-dev']
    for dep in build_deps:
        if not install_package(dep):
            return False
        print(f"✓ {dep} est installé")

    # Installer les dépendances Python requises
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()

    for requirement in requirements:
        if not install_package(requirement, use_pip=True):
            return False

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

    # Configurer Redis
    if not setup_redis():
        return False

    # Configurer MySQL
    if not setup_mysql():
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
