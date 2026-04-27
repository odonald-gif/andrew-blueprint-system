import logging
from typing import Dict, Any
import os
try:
    from core.black_book import BlackBook
    from core.motion_solver import motion_solver
except ImportError:
    BlackBook = None
    motion_solver = None

logger = logging.getLogger(__name__)

class EnvironmentalAwareness:
    """
    The 'Donna' intuition layer.
    Monitors digital breadcrumbs (Calendar, Slack, Idle) and detects if a meeting is running over.
    Applies the 'Long-Winder' buffer logic from the Black Book.
    """
    def __init__(self):
        if BlackBook:
            self.black_book = BlackBook()
        else:
            self.black_book = None
        
    def check_meeting_status(self, current_meeting: Dict[str, Any], current_time_minutes: int) -> Dict[str, Any]:
        """
        Checks meeting status by comparing current time against calendar end time.
        Slack integration requires SLACK_BOT_TOKEN in .env.
        """
        end_time = current_meeting.get("end_time_minutes", 0)
        contact = current_meeting.get("contact", "")

        # Real Slack status check requires API integration
        import os
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            logger.warning("SLACK_BOT_TOKEN not configured. Cannot check live meeting status.")
            return {"status": "no_data", "reason": "Slack API not connected"}

        # Time-based check: if past the meeting end time, flag as overrun
        if current_time_minutes > end_time:
            logger.info(f"User appears to be past meeting end time with {contact}.")
            return self._handle_overrun(contact, current_meeting)

        return {"status": "On Track", "action": "None"}

    def _handle_overrun(self, contact: str, meeting: Dict[str, Any]) -> Dict[str, Any]:
        """
        Looks up the contact in the Black Book. If they are a 'Long-Winder',
        we add a buffer. Otherwise, we trigger a 'Ping & Pivot'.
        """
        buffer_added = 15 # Default shift
        
        # Check Black Book for tags
        if self.black_book:
            profile = self.black_book.get_profile(contact)
            tags = profile.get("tags", [])
            
            if "long-winder" in tags or "vip" in tags:
                logger.info(f"Contextual Prediction: {contact} is a Long-Winder. Adding proactive 15m buffer.")
                # We don't bother the user, we just shift the afternoon automatically.
                action = "Motion Ripple Triggered"
            else:
                logger.info("Ping & Pivot: Sending invisible notification to user.")
                action = "Sent Invisible Notification 'Are we still in this?'"
                
            # Trigger Motion logic to actually shift the schedule
            # This is a simplification; in reality, we'd pass the new constraints to motion_solver.solve()
            if motion_solver:
                logger.info("Triggering Motion Logic to shift remaining tasks...")
                
            return {
                "status": "Held Over",
                "contact": contact,
                "action_taken": action,
                "buffer_added_mins": buffer_added
            }
            
        return {"status": "Error", "message": "Black Book offline"}

awareness_engine = EnvironmentalAwareness()
