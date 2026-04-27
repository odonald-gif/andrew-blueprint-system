import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryBank:
    """
    The Long-Term Experience Ledger.
    Records failures and successes so Andrew never makes the same mistake twice.
    """
    def __init__(self, filepath: str = "LESSONS.md"):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                f.write("# Andrew's Experience Ledger (Long-Term Memory)\n\n")

    def log_lesson(self, task_name: str, outcome: str, insight: str):
        """
        Logs a lesson learned to the Markdown ledger.
        """
        logger.info(f"Logging lesson for task: {task_name}")
        entry = f"## {task_name} ({datetime.now().strftime('%Y-%m-%d')})\n"
        entry += f"- **Outcome**: {outcome}\n"
        entry += f"- **Insight**: {insight}\n\n"
        
        with open(self.filepath, "a") as f:
            f.write(entry)
            
    def query_past_experience(self, context: str) -> str:
        """
        Retrieves past context before starting a new task.
        """
        logger.info(f"Querying Long-Term Memory for context: {context}")
        if not os.path.exists(self.filepath):
            return ""
        try:
            with open(self.filepath, "r") as f:
                content = f.read()
            return content[-2000:] if content else ""
        except Exception as e:
            logger.error(f"Failed to read LESSONS.md: {e}")
            return ""

memory_bank = MemoryBank()
