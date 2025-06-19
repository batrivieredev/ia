import sqlite3
import os
from pathlib import Path

class Database:
    def __init__(self):
        self.db_path = Path(__file__).parent / 'users.db'
        self.init_db()

    def init_db(self):
        """Initialize the database with schema"""
        if not self.db_path.parent.exists():
            os.makedirs(self.db_path.parent)

        conn = sqlite3.connect(self.db_path)
        with open(Path(__file__).parent / 'init.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()

    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)

    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, is_admin FROM users WHERE username = ? AND password = ?',
                      (username, password))
        result = cursor.fetchone()
        conn.close()
        return result if result else None

    def get_users(self):
        """Get all users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, is_admin, created_at FROM users')
        users = cursor.fetchall()
        conn.close()
        return users

    def create_user(self, username, password, is_admin=False):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                         (username, password, is_admin))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        conn.close()
        return success

    def update_user(self, user_id, username, password, is_admin):
        """Update a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if password:
                cursor.execute('UPDATE users SET username = ?, password = ?, is_admin = ? WHERE id = ?',
                             (username, password, is_admin, user_id))
            else:
                cursor.execute('UPDATE users SET username = ?, is_admin = ? WHERE id = ?',
                             (username, is_admin, user_id))
            conn.commit()
            success = cursor.rowcount > 0
        except sqlite3.IntegrityError:
            success = False
        conn.close()
        return success

    def delete_user(self, user_id):
        """Delete a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ? AND username != "admin"', (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

# Initialize database on import
db = Database()
