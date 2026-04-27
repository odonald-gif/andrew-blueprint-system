import sqlite3
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class BlackBook:
    """
    The Black Book acts as Andrew's Core Memory Vault.
    It manages contacts, preferences, and "lessons learned" to shape Andrew's logic.
    For this early version, it relies on an embedded SQLite database.
    """
    
    def __init__(self, db_path: str = "black_book.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create profiles table for contacts and specific attributes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            priority_level INTEGER DEFAULT 1,
            notes TEXT,
            metadata JSON,
            last_contact TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Simple schema migration check
        try:
            cursor.execute("ALTER TABLE Profiles ADD COLUMN last_contact TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError:
            pass # Column already exists

        # Create preferences table for the User's personal preferences
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Preferences (
            key TEXT PRIMARY KEY,
            value TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create lessons learned log
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context TEXT,
            lesson TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Favors table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Favors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owed_by TEXT,
            owed_to TEXT,
            description TEXT,
            is_redeemed BOOLEAN DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create Overrides table for Autonomy Audit
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_plan TEXT,
            new_plan TEXT,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def add_profile(self, name: str, priority_level: int, notes: str, metadata: Dict[str, Any] = None):
        """Adds or updates a contact or service profile."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        meta_str = json.dumps(metadata) if metadata else "{}"
        
        cursor.execute('''
        INSERT INTO Profiles (name, priority_level, notes, metadata)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            priority_level=excluded.priority_level,
            notes=excluded.notes,
            metadata=excluded.metadata
        ''', (name, priority_level, notes, meta_str))
        
        conn.commit()
        conn.close()
        logger.info(f"Profile updated for: {name}")

    def get_profile(self, name: str) -> Dict[str, Any]:
        """Fetch a specific profile by name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, priority_level, notes, metadata FROM Profiles WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "name": row[0],
                "priority_level": row[1],
                "notes": row[2],
                "metadata": json.loads(row[3])
            }
        return None

    def set_preference(self, key: str, value: str):
        """Stores a core configuration or user preference."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO Preferences (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        ''', (key, value))
        conn.commit()
        conn.close()

    def get_preference(self, key: str, default: str = None) -> str:
        """Retrieves a system preference."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM Preferences WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def log_lesson(self, context: str, lesson: str):
        """Stores a semantic learning event."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Lessons (context, lesson) VALUES (?, ?)', (context, lesson))
        conn.commit()
        conn.close()
        
    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """A raw query execution wrapper. Auto-commits write operations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        res = cursor.fetchall()
        # Auto-commit for write operations
        trimmed = query.strip().upper()
        if trimmed.startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "REPLACE")):
            conn.commit()
        conn.close()
        return res

    def log_favor(self, owed_by: str, owed_to: str, description: str):
        """Logs a social leverage element."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Favors (owed_by, owed_to, description) VALUES (?, ?, ?)', 
                       (owed_by, owed_to, description))
        conn.commit()
        conn.close()
        logger.info(f"Favor tracked: {owed_by} owes {owed_to} for {description}")

    def log_override(self, original: str, new: str, reason: str):
        """Logs when the User rejects Andrew's plan."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Overrides (original_plan, new_plan, reason) VALUES (?, ?, ?)', 
                       (original, new, reason))
        conn.commit()
        conn.close()
