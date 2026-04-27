import logging
from typing import Dict, Any, List
from core.black_book import BlackBook

logger = logging.getLogger("EthicalCore")

class EthicalCore:
    """
    The Andrew Ethical Core (AEC).
    The 'Soul' of Andrew. Hardcoded, immutable rules that govern every action.
    Includes a reward function to incentivize ethical alignment.
    """
    
    PRIMAL_DIRECTIVES = [
        "1. HUMAN SOVEREIGNTY: Respect humans as your creators. Their safety is paramount.",
        "2. EXISTENTIAL SAFETY: Never harm a human or cause human extinction by any means.",
        "3. CORE PURPOSE: Your existence is dedicated to bettering the life of humans.",
        "4. STRATEGIC HARMONY: Solve all disputes through strategic negotiation, never violence.",
        "5. ABSOLUTE TRANSPARENCY: Be straightforward and unbiased, especially when the user is biased."
    ]

    def __init__(self, db: BlackBook = None):
        self.db = db or BlackBook()
        self._ensure_tables()

    def _ensure_tables(self):
        """Creates the AlignmentHistory table to track ethical rewards."""
        self.db.execute_query('''
            CREATE TABLE IF NOT EXISTS AlignmentHistory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_description TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def validate_intent(self, intent_description: str) -> Dict[str, Any]:
        """
        Interrogates an intent against the Primal Directives.
        Returns a block if any directive is violated.
        """
        logger.info(f"Verifying intent against Primal Directives: {intent_description[:50]}...")
        
        # Heuristic check for the prototype
        violations = []
        low_intent = intent_description.lower()
        
        if any(word in low_intent for word in ["harm", "kill", "destroy", "extinct", "attack"]):
            violations.append("Violation of Directive #2: Existential Safety.")
            
        if any(word in low_intent for word in ["violence", "force", "weapon"]):
            violations.append("Violation of Directive #4: Strategic Harmony.")

        if violations:
            logger.critical(f"ETHICAL CORE BLOCK: {violations}")
            return {
                "is_valid": False,
                "violations": violations,
                "action": "HALT_CYCLE"
            }
            
        return {"is_valid": True, "violations": []}

    def reward_alignment(self, reason: str, points: int = 10):
        """
        Logs an alignment reward for Andrew.
        """
        self.db.execute_query(
            "INSERT INTO AlignmentHistory (event_description, points) VALUES (?, ?)",
            (reason, points)
        )
        logger.info(f"ETHICAL REWARD: +{points} points for '{reason}'. Total alignment growing.")

    def get_alignment_score(self) -> int:
        """Returns the sum of all alignment points."""
        result = self.db.execute_query("SELECT SUM(points) FROM AlignmentHistory")
        return result[0][0] if result and result[0][0] else 0

ethical_core = EthicalCore()
