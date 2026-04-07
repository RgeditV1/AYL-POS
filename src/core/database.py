import sqlite3
import os
from src.core.config import DB_PATH

class DatabaseManager:
    """Handles SQLite database connection and schema initialization."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.initialize_db()

    def get_connection(self):
        """Returns a sqlite3 Connection object with Row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_db(self):
        """Creates tables if they do not exist."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            """)

            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    precio REAL DEFAULT 0.0,
                    cantidad INTEGER DEFAULT 0,
                    costo REAL DEFAULT 0.0
                )
            """)

            # Tickets table (Header)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    fecha_hora TEXT NOT NULL,
                    cajero TEXT NOT NULL,
                    total REAL DEFAULT 0.0,
                    estado TEXT DEFAULT 'activa'
                )
            """)

            # Sale Items table (Lines)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    codigo TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id)
                )
            """)

            # Cash Flow table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cash_flow (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_hora TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    monto REAL NOT NULL,
                    concepto TEXT
                )
            """)

            conn.commit()
        finally:
            conn.close()

# Singleton instance
_db_manager = None

def get_db_manager():
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
