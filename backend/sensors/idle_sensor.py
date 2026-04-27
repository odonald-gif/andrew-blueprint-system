import time
import logging

logger = logging.getLogger(__name__)

class IdleSensor:
    """
    Simulates checking for System Idleness to determine if a meeting ran too long.
    If the system is perfectly idle during a scheduled 'Deep Work' block, Andrew
    knows the user is actually working. If it's active during a 'Meeting', but the meeting ends,
    Andrew might interrupt.
    """
    def __init__(self, idle_threshold_seconds: int = 300):
        self.idle_threshold = idle_threshold_seconds
        
    def check_idle_state(self) -> bool:
        """
        Uses psutil to check if CPU usage is below 5%, which implies idleness on a server.
        """
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.5)
            return cpu_percent < 5.0
        except Exception as e:
            logger.warning(f"Failed to read CPU activity: {e}. Assuming active (False).")
            return False
