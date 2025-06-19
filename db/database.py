import mysql.connector
from mysql.connector import pooling
import os
import redis
from pathlib import Path
import json

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

        # Initialize connection pool
        self.pool = mysql.connector.pooling.MySQLConnectionPool(**self.pool_config)

        # Initialize Redis
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1 hour cache

        self.init_db()

    def init_db(self):
        """Initialize the database with schema"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                with open(Path(__file__).parent / 'init_mysql.sql', 'r') as f:
                    for statement in f.read().split(';'):
                        if statement.strip():
                            cursor.execute(statement)
            conn.commit()
        finally:
            conn.close()

    def get_connection(self):
        """Get a database connection from the pool"""
        return self.pool.get_connection()

    def verify_user(self, username, password):
        """Verify user credentials"""
        cache_key = f"auth:{username}:{password}"

        # Check cache first
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT id, is_admin FROM users WHERE username = %s AND password = %s',
                    (username, password)
                )
                result = cursor.fetchone()
                if result:
                    # Cache successful login
                    self.redis.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(result)
                    )
                return result if result else None
        finally:
            conn.close()

    def get_users(self):
        """Get all users"""
        cache_key = "users:all"

        # Check cache first
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        conn = self.get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    'SELECT id, username, is_admin, created_at FROM users'
                )
                users = cursor.fetchall()

                # Cache the results
                self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps([{**user, 'created_at': user['created_at'].isoformat()} for user in users])
                )
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
            # Invalidate caches
            self.redis.delete("users:all")
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
            success = cursor.rowcount > 0
            if success:
                # Invalidate caches
                self.redis.delete("users:all")
                self.redis.delete(f"user:{user_id}")
            return success
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
            success = cursor.rowcount > 0
            if success:
                # Invalidate caches
                self.redis.delete("users:all")
                self.redis.delete(f"user:{user_id}")
            return success
        finally:
            conn.close()

# Initialize database on import
db = Database()
