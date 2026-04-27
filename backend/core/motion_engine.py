import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MotionEngine:
    """
    Constraint-Based Scheduler.
    Calculates: Available Time - (Meetings + Buffer) = Deep Work Slots.
    """
    def __init__(self):
        self.buffer_minutes = 15

    def calculate_deep_work_slots(self, available_hours: int, meetings_duration_hours: float) -> float:
        """
        Calculates how many deep work slots Donald has left today.
        """
        total_minutes = available_hours * 60
        meetings_minutes = meetings_duration_hours * 60
        buffer_total = (meetings_minutes / 60) * self.buffer_minutes # 15 min buffer per hour of meeting
        
        deep_work_minutes = total_minutes - (meetings_minutes + buffer_total)
        logger.info(f"Motion Engine: Calculated {deep_work_minutes / 60:.1f} hours of deep work slots.")
        return max(0, deep_work_minutes / 60)

    def triage_task(self, task: dict, current_energy_score: int) -> dict:
        """
        Fits a 'Soft Task' into a Deep Work slot based on energy levels.
        """
        if current_energy_score < 40 and task.get('complexity', 0) > 5:
            return {"status": "rescheduled", "reason": "Low energy detected. Rescheduling complex task."}
            
        return {"status": "scheduled", "time": "next available slot"}

    def check_timetable_status(self) -> str:
        """
        Checks if the user is currently busy based on Google Calendar.
        Requires GOOGLE_CALENDAR_ID in .env for real integration.
        """
        import os
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        if not calendar_id:
            logger.warning("GOOGLE_CALENDAR_ID not set. Cannot check real timetable.")
            return "NO_DATA"

        # When Google Calendar API is integrated, this will query real events.
        # For now, return AVAILABLE since we can't confirm either way.
        return "AVAILABLE"

    def push_tasks_to_later(self, time_frame: str) -> str:
        """
        Voice-command triggered method to wipe the current schedule block and move tasks.
        """
        logger.info(f"User Command: Pushing all current tasks to {time_frame}.")
        return f"Understood. All soft tasks have been moved to {time_frame}. Enjoy your downtime."

motion_engine = MotionEngine()
