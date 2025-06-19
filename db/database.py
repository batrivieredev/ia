import psycopg2
import os
from pathlib import Path

class Database:
    def __init__(self):
        self.conn_params = {
            'dbname': 'ia_chat',
            'user': 'ia_user',
            'password': 'ia_password',  # Même mot de passe que dans requirements.py
            'host': 'localhost',
            'port': 5432
        }
        self.init_db()

    def init_db(self):
        """Initialize the database with schema"""
        conn = self.get_connection()
        with conn.cursor() as cursor:
            with open(Path(__file__).parent / 'init_postgres.sql', 'r') as f:
                cursor.execute(f.read())
        conn.commit()
        conn.close()

    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(**self.conn_params)

    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = self.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id, is_admin FROM users WHERE username = %s AND password = %s',
                (username, password)
            )
            result = cursor.fetchone()
        conn.close()
        return result if result else None

    def get_users(self):
        """Get all users"""
        conn = self.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id, username, is_admin, created_at FROM users'
            )
            users = cursor.fetchall()
        conn.close()
        return users

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
            success = True
        except psycopg2.IntegrityError:
            conn.rollback()
            success = False
        finally:
            conn.close()
        return success

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
            success = cursor.rowcount > 0
        except psycopg2.IntegrityError:
            conn.rollback()
            success = False
        finally:
            conn.close()
        return success

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
            success = cursor.rowcount > 0
        finally:
            conn.close()
        return success

# Initialize database on import
db = Database()
