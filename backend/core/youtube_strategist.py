import logging
from core.persona import PersonaEngine

logger = logging.getLogger("YouTubeStrategist")

class YouTubeStrategist:
    """
    Hunts for high-CPM trending topics and generates engaging video scripts.
    """
    def __init__(self):
        self.ai = PersonaEngine()

    def generate_viral_script(self, niche: str = "Technology & AI", analytics_report: dict = None) -> dict:
        """
        Uses Gemini to generate a high-retention video script, adjusting based on past analytics.
        """
        logger.info(f"Generating viral script for niche: {niche}")
        
        analytics_context = ""
        if analytics_report and analytics_report.get("status") == "success":
            avg_duration = analytics_report.get('average_view_duration_seconds', 0)
            insight = analytics_report.get('insight', '')
            analytics_context = f"\nCRITICAL DATA: Your last videos averaged {avg_duration} seconds of watch time. {insight}. Adjust your script structure accordingly (e.g., if drop-off is high, make the intro much faster)."
        
        prompt = f"""
        You are an elite YouTube strategist and scriptwriter specializing in the {niche} niche.
        Write a highly engaging, 3-minute video script on a currently trending topic.
        {analytics_context}
        
        Requirements:
        1. Start with an intense, hook-driven intro (first 5 seconds).
        2. Keep sentences short and punchy for TTS narration.
        3. Break the script into [SCENE] and [NARRATION] blocks.
        4. Focus on high CPM topics (e.g., AI automation, wealth generation, software architecture).
        5. Provide a clickbait-style but accurate Video Title at the very top.
        """
        
        script_content = self.ai.process_user_feedback(prompt)
        
        # Simple extraction logic
        lines = script_content.split('\n')
        title = "Automated Video"
        if lines and "title:" in lines[0].lower():
            title = lines[0].split(":", 1)[1].strip()
            
        logger.info(f"Script generated. Title: {title}")
        
        return {
            "status": "success",
            "title": title,
            "script": script_content
        }

youtube_strategist = YouTubeStrategist()
