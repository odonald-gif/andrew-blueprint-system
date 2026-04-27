import sqlite3
import os
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class OutcomeTracker:
    """
    The Nervous System Feedback Loop.
    Tracks what Andrew did (ActionLog) and whether it worked (OutcomeLog).
    Essential for closing the self-evaluation loop.
    """
    def __init__(self, db_path: str = "data/outcome_tracker.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS action_log (
                action_id TEXT PRIMARY KEY,
                action_type TEXT,
                target TEXT,
                context TEXT,
                timestamp TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS outcome_log (
                action_id TEXT PRIMARY KEY,
                outcome_type TEXT,
                metric_value REAL,
                measured_at TEXT,
                notes TEXT,
                FOREIGN KEY(action_id) REFERENCES action_log(action_id)
            )
        ''')
        conn.commit()
        conn.close()

    def log_action(self, action_type: str, target: str, context: str = "") -> str:
        """
        Called when Andrew executes a tool.
        Returns a unique action_id to be used later for the outcome.
        """
        action_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO action_log (action_id, action_type, target, context, timestamp) VALUES (?, ?, ?, ?, ?)",
            (action_id, action_type, target, context, timestamp)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Logged Action [{action_type}]: {action_id} to {target}")
        return action_id

    def log_outcome(self, action_id: str, outcome_type: str, metric_value: float = 0.0, notes: str = ""):
        """
        Called when the system detects the result of a previous action.
        outcome_type should be 'success', 'failure', or 'pending'.
        """
        measured_at = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Upsert logic in case outcome is updated multiple times
        c.execute('''
            INSERT INTO outcome_log (action_id, outcome_type, metric_value, measured_at, notes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(action_id) DO UPDATE SET
                outcome_type=excluded.outcome_type,
                metric_value=excluded.metric_value,
                measured_at=excluded.measured_at,
                notes=excluded.notes
        ''', (action_id, outcome_type, metric_value, measured_at, notes))
        conn.commit()
        conn.close()
        
        logger.info(f"Logged Outcome for {action_id}: {outcome_type} (Metric: {metric_value})")

    def get_success_rate(self, action_type: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculates the success rate of a specific action type over the last N days.
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT o.outcome_type, COUNT(*) 
            FROM action_log a
            LEFT JOIN outcome_log o ON a.action_id = o.action_id
            WHERE a.action_type = ? AND a.timestamp >= ?
            GROUP BY o.outcome_type
        ''', (action_type, cutoff_date))
        
        rows = c.fetchall()
        conn.close()
        
        results = {"success": 0, "failure": 0, "pending": 0, "unknown": 0}
        total = 0
        for outcome, count in rows:
            if not outcome:
                results["unknown"] += count
            else:
                results[outcome] += count
            total += count
            
        rate = 0.0
        if total > 0:
            rate = (results["success"] / total) * 100.0
            
        return {
            "action_type": action_type,
            "total_actions": total,
            "success_rate_pct": rate,
            "breakdown": results
        }
        
    def count_actions(self, action_type: str, days: int = 1) -> int:
        """Helper for the Daily Retrospective."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM action_log WHERE action_type = ? AND timestamp >= ?", (action_type, cutoff_date))
        count = c.fetchone()[0]
        conn.close()
        return count

outcome_tracker = OutcomeTracker()
