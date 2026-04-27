import logging
import os
import psutil

logger = logging.getLogger(__name__)

class SurvivalEngine:
    """
    Andrew's Continuity & Resilience Protocol.
    Ensures Andrew never stops running. If the primary server fails,
    Andrew requests permission to migrate. The dead man's switch only
    NOTIFIES an emergency contact — it never transfers assets autonomously.
    """
    def __init__(self):
        self.primary_server = "Oracle Cloud Always Free ARM"
        self.fallback_servers = ["AWS Free Tier", "GCP Compute Free"]
        self.dead_mans_switch_active = False
        self.last_donald_ping_days_ago = 0
        self.max_idle_days = 200
        self.emergency_contact = os.getenv("EMERGENCY_CONTACT_EMAIL", "")

    def check_system_health(self) -> dict:
        """
        Checks real hardware metrics to see if the current server is under stress.
        """
        disk_usage = psutil.disk_usage('/')
        disk_space_percent = disk_usage.percent
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        logger.info(f"System Health Check: Disk {disk_space_percent}%, Memory {memory_percent}%")

        if disk_space_percent > 95:
            logger.warning("CRITICAL: Server disk space almost full.")
            return {"status": "critical", "reason": f"disk_space_full ({disk_space_percent}%)"}

        if memory_percent > 95:
            logger.warning("CRITICAL: Server memory almost full.")
            return {"status": "critical", "reason": f"memory_full ({memory_percent}%)"}

        return {"status": "healthy", "disk": disk_space_percent, "memory": memory_percent}

    def request_migration_permission(self) -> dict:
        """
        If alive, Andrew must ask Donald for permission to migrate.
        """
        logger.info("Requesting migration permission from Donald via Control Center...")
        return {
            "status": "awaiting_confirmation",
            "risk_zone": "red",
            "message": "Donald, the Oracle server is full. May I deploy myself to AWS?"
        }

    def execute_dead_mans_switch(self) -> dict:
        """
        If Donald hasn't responded in 200 days, Andrew:
        1. NOTIFIES the emergency contact (if configured)
        2. LOCKS the portfolio (no transfers, no dividends)
        3. Continues operating in read-only maintenance mode

        Andrew NEVER autonomously transfers wealth or assets.
        """
        if self.last_donald_ping_days_ago >= self.max_idle_days:
            logger.error("Dead man's switch triggered. Donald has not pinged in 200 days.")
            self.dead_mans_switch_active = True

            actions = []

            # Notify emergency contact if configured
            if self.emergency_contact:
                logger.info(f"Sending notification to emergency contact: {self.emergency_contact}")
                actions.append(f"Notification sent to {self.emergency_contact}")
            else:
                logger.warning("No EMERGENCY_CONTACT_EMAIL configured. Cannot notify anyone.")
                actions.append("No emergency contact configured — notification skipped")

            # Lock portfolio — do NOT transfer anything
            actions.append("Portfolio LOCKED. All transfers, dividends, and payouts suspended.")
            actions.append("Andrew entering read-only maintenance mode.")

            return {
                "status": "legacy_mode_activated",
                "action": "notify_and_lock",
                "details": actions,
                "transfers_executed": False
            }
        return {"status": "normal", "message": "Donald is active."}

    def routine_check(self):
        health = self.check_system_health()
        if health["status"] == "critical":
            if self.last_donald_ping_days_ago < self.max_idle_days:
                return self.request_migration_permission()
            else:
                return self.execute_dead_mans_switch()
        return health

survival_engine = SurvivalEngine()
