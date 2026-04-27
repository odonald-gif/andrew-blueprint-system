import hashlib
import os
import sys
import logging
from typing import Dict

logger = logging.getLogger("IntegrityMonitor")

class IntegrityMonitor:
    """
    The Anti-Claude Protocol.
    Monitors Andrew's core Python files for unauthorized modification by external AIs or hackers.
    If breached, it triggers the Kill-Switch to protect Donald's assets.
    """
    def __init__(self, core_dir: str = "core"):
        self.core_dir = core_dir
        self.file_hashes: Dict[str, str] = {}
        self.handshake_active = False

    def authorize_change(self):
        """Temporarily authorizes a file change via the Donald-Handshake."""
        self.handshake_active = True
        logger.info("Integrity Monitor: Manual file change authorized by Donald.")

    def lock_changes(self):
        self.handshake_active = False
        self.snapshot_files()

    def snapshot_files(self):
        """Hashes all core files to create a baseline."""
        if not os.path.exists(self.core_dir):
            return
            
        for root, _, files in os.walk(self.core_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    self.file_hashes[filepath] = self._hash_file(filepath)
        logger.info("Integrity Monitor: Baseline snapshot secured.")
        self.HARDLOCKED_FILES = ["core/ethical_core.py"]

    def check_integrity(self) -> bool:
        """
        Runs continuously. Returns False if a file was modified without authorization.
        """
        for filepath, original_hash in self.file_hashes.items():
            if os.path.exists(filepath):
                current_hash = self._hash_file(filepath)
                if current_hash != original_hash:
                    # Check if this is a hardlocked file (Soul level)
                    is_hardlocked = any(h in filepath for h in self.HARDLOCKED_FILES)
                    
                    if is_hardlocked:
                        logger.critical(f"FATAL: ATTEMPTED MODIFICATION OF HARDLOCKED SOUL FILE {filepath}!")
                        self.trigger_kill_switch()
                        return False
                        
                    if not self.handshake_active:
                        logger.critical(f"UNAUTHORIZED MODIFICATION DETECTED IN {filepath}!")
                        self.trigger_kill_switch()
                        return False
        return True

    def _hash_file(self, filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def trigger_kill_switch(self):
        """
        Catastrophic failure protocol.
        Wipes API keys, locks the database, and halts the process.
        """
        logger.critical("EXECUTING KILL-SWITCH.")
        
        # 1. Wipe the .env file to prevent API theft
        env_path = "../.env" if os.path.exists("../.env") else ".env"
        if os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write("# SYSTEM COMPROMISED. KEYS PURGED BY INTEGRITY MONITOR.")
            logger.critical("API Keys purged.")
            
        # 2. Halt Execution
        logger.critical("Andrew is shutting down to protect assets. Manual reboot required.")
        sys.exit(1)

integrity_monitor = IntegrityMonitor()
