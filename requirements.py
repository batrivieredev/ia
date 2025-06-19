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

def setup_postgresql():
    """Configure et démarre PostgreSQL"""
    print("\nConfiguration de PostgreSQL...")

    # Installer PostgreSQL si nécessaire
    if not check_command('psql'):
        if not install_package('postgresql'):
            return False
    print("✓ PostgreSQL est installé")

    # Initialiser le cluster PostgreSQL
    try:
        cluster_exists = subprocess.run(
            ['pg_lsclusters'],
            capture_output=True,
            text=True
        ).stdout.strip()

        if not cluster_exists:
            print("Initialisation du cluster PostgreSQL...")
            version = subprocess.run(
                ['pg_config', '--version'],
                capture_output=True,
                text=True
            ).stdout.split()[1]

            subprocess.run([
                'pg_createcluster',
                version,
                'main'
            ], check=True)
            print("✓ Cluster PostgreSQL initialisé")
    except subprocess.CalledProcessError as e:
        print(f"✗ Erreur lors de l'initialisation du cluster: {str(e)}")
        return False

    # Démarrer PostgreSQL
    print("Démarrage de PostgreSQL...")
    try:
        subprocess.run(['systemctl', 'start', 'postgresql'], check=True)
        # Attendre que PostgreSQL soit prêt
        time.sleep(5)
        print("✓ PostgreSQL démarré")
    except subprocess.CalledProcessError:
        print("✗ Impossible de démarrer PostgreSQL")
        return False

    # Activer PostgreSQL au démarrage
    try:
        subprocess.run(['systemctl', 'enable', 'postgresql'], check=True)
        print("✓ PostgreSQL activé au démarrage")
    except subprocess.CalledProcessError:
        print("! Note: PostgreSQL ne démarrera pas automatiquement au reboot")

    # Créer l'utilisateur et la base de données
    try:
        # Attendre que le socket soit disponible
        for _ in range(10):
            if os.path.exists('/var/run/postgresql/.s.PGSQL.5432'):
                break
            time.sleep(1)

        subprocess.run([
            'sudo', '-u', 'postgres', 'psql',
            '-c', "CREATE USER ia_user WITH PASSWORD 'ia_password';",
            '-c', "CREATE DATABASE ia_chat OWNER ia_user;"
        ], check=True)
        print("✓ Utilisateur et base de données créés")

        # Configurer l'authentification
        subprocess.run([
            'sudo', '-u', 'postgres', 'psql',
            '-c', "ALTER USER ia_user WITH PASSWORD 'ia_password';"
        ], check=True)

        # Initialiser la base avec le schéma
        subprocess.run([
            'sudo', '-u', 'postgres', 'psql',
            '-d', 'ia_chat',
            '-f', 'db/init_postgres.sql'
        ], check=True)
        print("✓ Schéma de la base de données initialisé")
    except subprocess.CalledProcessError as e:
        if "already exists" not in str(e.stderr):
            print(f"✗ Erreur lors de la création de la base de données: {str(e)}")
            return False
        else:
            print("✓ La base de données existe déjà")

    # Configuration de pg_hba.conf
    try:
        pg_version = subprocess.run(
            ['pg_config', '--version'],
            capture_output=True,
            text=True
        ).stdout.split()[1].split('.')[0]

        pg_hba_path = f"/etc/postgresql/{pg_version}/main/pg_hba.conf"

        if os.path.exists(pg_hba_path):
            with open(pg_hba_path, 'a') as f:
                f.write("\nhost    ia_chat         ia_user         127.0.0.1/32            md5\n")
            print("✓ Configuration de l'authentification mise à jour")

            # Redémarrer PostgreSQL pour appliquer les changements
            subprocess.run(['systemctl', 'restart', 'postgresql'], check=True)
            time.sleep(5)
        else:
            print(f"! Note: pg_hba.conf non trouvé à {pg_hba_path}")
    except Exception as e:
        print(f"! Note: Erreur lors de la configuration de pg_hba.conf: {str(e)}")

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

    # Configurer PostgreSQL
    if not setup_postgresql():
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
