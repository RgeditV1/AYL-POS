import base64
import hashlib
import hmac
import os
from src.core.config import CREDENTIALS_FILE

class UserManager:
    """Manages user authentication and authorization with secure hashing."""

    def __init__(self, credentials_file=None):
        self.credentials_file = credentials_file or CREDENTIALS_FILE
        self.ensure_credentials_file()

    def ensure_credentials_file(self):
        """Ensure the credentials file exists."""
        if not os.path.exists(self.credentials_file):
            # Create default admin user
            self.create_user("admin", "password", "admin", save_now=True)

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
            # Check for legacy base64 passwords
            if "$" not in stored_password:
                try:
                    decoded = base64.b64decode(stored_password).decode("utf-8")
                    return decoded == provided_password
                except Exception:
                    return False
            
            salt_hex, hash_hex = stored_password.split("$")
            salt = bytes.fromhex(salt_hex)
            pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(pwd_hash.hex(), hash_hex)
        except Exception:
            return False

    def create_user(self, username, password, role="cashier", save_now=True):
        """Create a new user with hashed password."""
        users = self.load_users()
        if username in users:
            return False, "El usuario ya existe."
            
        if role not in ["admin", "cashier"]:
            return False, "Rol inválido. Debe ser 'admin' o 'cashier'."

        hashed = self.hash_password(password)
        users[username] = {"password": hashed, "role": role}
        
        if save_now:
            self.save_users(users)
        return True, "Usuario creado exitosamente."

    def load_users(self):
        """Load all users from the credentials file."""
        users = {}
        if not os.path.exists(self.credentials_file):
            return users

        try:
            with open(self.credentials_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(":")
                    if len(parts) >= 3:
                        username, password_data, role = parts[0], parts[1], parts[2]
                        users[username] = {
                            "password": password_data,
                            "role": role,
                        }
        except Exception:
            pass
        return users

    def save_users(self, users):
        """Save all users to the credentials file."""
        try:
            with open(self.credentials_file, "w", encoding="utf-8") as f:
                for username, data in users.items():
                    f.write(f"{username}:{data['password']}:{data['role']}\n")
            return True, "Usuarios guardados."
        except Exception as e:
            return False, str(e)

    def authenticate(self, username, password):
        """Authenticate a user and return their role if successful."""
        users = self.load_users()
        if username in users:
            stored_password = users[username]["password"]
            if self.verify_password(stored_password, password):
                # Auto-migrate legacy passwords
                if "$" not in stored_password:
                    new_hash = self.hash_password(password)
                    users[username]["password"] = new_hash
                    self.save_users(users)
                return users[username]["role"]
        return None

    def list_users(self):
        """Return a dict of all users and roles (matching legacy expectation)."""
        return self.load_users()

    def delete_user(self, username):
        """Delete a user."""
        users = self.load_users()
        if username not in users:
            return False, "Usuario no encontrado."

        if username == "admin" and len([u for u in users if users[u]["role"] == "admin"]) == 1:
            return False, "No se puede eliminar el último administrador."

        del users[username]
        self.save_users(users)
        return True, "Usuario eliminado exitosamente."

    def change_password(self, username, new_password):
        """Change user password."""
        users = self.load_users()
        if username not in users:
            return False, "Usuario no encontrado."

        users[username]["password"] = self.hash_password(new_password)
        self.save_users(users)
        return True, "Contraseña actualizada exitosamente."
