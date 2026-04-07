import hashlib
import hmac
import os
from src.core.database import get_db_manager

class UserManager:
    """Manages user authentication and authorization using SQLite."""

    def __init__(self):
        self.db = get_db_manager()
        self.ensure_admin_exists()

    def ensure_admin_exists(self):
        """Ensure at least one admin exists in the database."""
        users = self.load_users()
        if not users:
            self.create_user("admin", "admin", "admin")

    def hash_password(self, password, salt=None):
        """Hash a password using pbkdf2_hmac."""
        if salt is None:
            salt = os.urandom(16)
        else:
            if isinstance(salt, str):
                salt = bytes.fromhex(salt)
        
        # 100,000 iterations of SHA256
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + "$" + pwd_hash.hex()

    def verify_password(self, stored_password, provided_password):
        """Verify a stored password against a provided password."""
        try:
            if "$" not in stored_password:
                # Legacy support could be added here if needed during migration
                return False
            
            salt_hex, hash_hex = stored_password.split("$")
            salt = bytes.fromhex(salt_hex)
            pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(pwd_hash.hex(), hash_hex)
        except Exception:
            return False

    def create_user(self, username, password, role="cajero"):
        """Create a new user in the database."""
        if role not in ["admin", "cajero"]:
            return False, "Rol inválido."

        password_hash = self.hash_password(password)
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            return True, "Usuario creado exitosamente."
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                return False, "El usuario ya existe."
            return False, str(e)
        finally:
            conn.close()

    def authenticate(self, username, password):
        """Authenticate a user and return their role if successful."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row and self.verify_password(row["password_hash"], password):
                return row["role"]
        except Exception:
            pass
        finally:
            conn.close()
        return None

    def load_users(self):
        """Return a dict of all users and roles."""
        conn = self.db.get_connection()
        users = {}
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username, role FROM users")
            for row in cursor.fetchall():
                users[row["username"]] = {"role": row["role"]}
        except Exception:
            pass
        finally:
            conn.close()
        return users

    def delete_user(self, username):
        """Delete a user from the database."""
        if username == "admin":
            # Extra check to avoid deleting the main admin
            users = self.load_users()
            admins = [u for u in users if users[u]["role"] == "admin"]
            if len(admins) <= 1:
                return False, "No se puede eliminar el último administrador."

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return True, "Usuario eliminado exitosamente."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def change_password(self, username, new_password):
        """Update a user's password."""
        new_hash = self.hash_password(new_password)
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
            conn.commit()
            return True, "Contraseña actualizada exitosamente."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
