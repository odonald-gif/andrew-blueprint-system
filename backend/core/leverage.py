import sqlite3
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LeverageTracker:
    """
    The Strategic Memory / Favor Tracker.
    Stores and retrieves social leverage so Andrew knows who "owes you one."
    """
    def __init__(self, db_name="favors.db"):
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db', db_name))
        self._init_db()

    def _init_db(self):
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact TEXT NOT NULL,
                    value TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Owed',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def log_favor(self, contact: str, value: str, status: str = "Owed"):
        """Logs a favor that was performed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO favors (contact, value, status) VALUES (?, ?, ?)",
                    (contact, value, status)
                )
                conn.commit()
            logger.info(f"Logged favor for {contact}: {value}")
            return True
        except Exception as e:
            logger.error(f"Error logging favor: {e}")
            return False

    def get_leverage(self, contact: str) -> List[Dict[str, Any]]:
        """Retrieves outstanding favors for a contact."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM favors WHERE contact = ? AND status = 'Owed' ORDER BY timestamp DESC",
                    (contact,)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving leverage for {contact}: {e}")
            return []

    def settle_favor(self, favor_id: int):
        """Marks a favor as cashed in/settled."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE favors SET status = 'Settled' WHERE id = ?",
                    (favor_id,)
                )
                conn.commit()
            logger.info(f"Favor {favor_id} marked as Settled.")
            return True
        except Exception as e:
            logger.error(f"Error settling favor: {e}")
            return False

leverage_tracker = LeverageTracker()
