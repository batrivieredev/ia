import mysql.connector
from mysql.connector import pooling, Error
import os
from pathlib import Path

class Database:
    def __init__(self):
        self.pool_config = {
            'pool_name': 'mypool',
            'pool_size': 5,
            'pool_reset_session': True,
            'host': 'localhost',
            'port': 3306,
            'database': 'ia_chat',
            'user': 'ia_user',
            'password': 'ia_password'
        }

        try:
            # Initialize connection pool
            self.pool = mysql.connector.pooling.MySQLConnectionPool(**self.pool_config)
            self.init_db()
        except Error as e:
            print(f"Erreur de connexion à la base de données: {str(e)}")
            raise

    def init_db(self):
        """Initialize the database with schema"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # Lire et exécuter le fichier SQL
                with open(Path(__file__).parent / 'init_mysql.sql', 'r') as f:
                    sql = f.read()

                # Exécuter chaque commande séparément
                for statement in sql.split(';'):
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                        except Error as e:
                            # Ignorer les erreurs de clé dupliquée ou de table existante
                            if not (e.errno == 1061 or e.errno == 1050):
                                raise
            conn.commit()
        except Error as e:
            print(f"Erreur d'initialisation de la base de données: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_connection(self):
        """Get a database connection from the pool"""
        return self.pool.get_connection()

    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT id, is_admin FROM users WHERE username = %s AND password = %s',
                    (username, password)
                )
                result = cursor.fetchone()
                return result if result else None
        finally:
            conn.close()

    def get_users(self):
        """Get all users"""
        conn = self.get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    'SELECT id, username, is_admin, created_at FROM users ORDER BY created_at DESC'
                )
                users = cursor.fetchall()

                # Convert datetime objects to string for JSON serialization
                for user in users:
                    user['created_at'] = user['created_at'].isoformat()
                return users
        finally:
            conn.close()

    def create_user(self, username, password, is_admin=False):
        """Create a new user"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)',
                    (username, password, is_admin)
                )
            conn.commit()
            return True
        except mysql.connector.IntegrityError:
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_user(self, user_id, username, password, is_admin):
        """Update a user"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                if password:
                    cursor.execute(
                        'UPDATE users SET username = %s, password = %s, is_admin = %s WHERE id = %s',
                        (username, password, is_admin, user_id)
                    )
                else:
                    cursor.execute(
                        'UPDATE users SET username = %s, is_admin = %s WHERE id = %s',
                        (username, is_admin, user_id)
                    )
            conn.commit()
            return cursor.rowcount > 0
        except mysql.connector.IntegrityError:
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_user(self, user_id):
        """Delete a user"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    'DELETE FROM users WHERE id = %s AND username != %s',
                    (user_id, 'admin')
                )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

try:
    # Initialize database on import
    db = Database()
except Exception as e:
    print(f"Erreur fatale lors de l'initialisation de la base de données: {str(e)}")
    raise
