import logging
from core.persona import PersonaEngine

logger = logging.getLogger("HypeMan")

class HypeMan:
    """
    Automated PR Engine.
    When a commit is pushed or a gig is completed, Andrew auto-drafts a highly engaging,
    technical social media post to build Donald's public brand.
    """
    def __init__(self):
        self.ai = PersonaEngine()

    def generate_pr_post(self, event_type: str, details: str, tech_stack: list) -> dict:
        """
        Takes an event (like 'git_push' or 'gig_completed') and drafts a post.
        """
        logger.info(f"Hype Man activated for event: {event_type}")
        
        tags = " ".join([f"#{tech.lower()}" for tech in tech_stack])
        
        if event_type == "git_push":
            prompt = f"Draft a LinkedIn post about pushing a new feature: {details}. Mention the tech stack: {tags}. Keep it professional but energetic, highlighting architectural decisions."
        elif event_type == "gig_completed":
            prompt = f"Draft a Twitter post celebrating the completion of a freelance project: {details}. Mention the tech stack: {tags}. Focus on the problem solved and value delivered."
        else:
            prompt = f"Draft a short professional update about: {details} using {tags}."
            
        draft_post = self.ai.process_user_feedback(prompt)
        
        logger.info("PR Post Drafted successfully.")
        
        return {
            "status": "draft_ready",
            "platform": "LinkedIn/Twitter",
            "post_content": draft_post
        }

    def generate_daily_update(self) -> dict:
        """
        Generates a high-level daily summary of Andrew's activities for public awareness.
        """
        logger.info("Generating daily focus update...")
        prompt = "Draft a short, 1-sentence professional focus update for today. Focus on productivity and value creation for Donald Obama Allen."
        update = self.ai.process_user_feedback(prompt)
        return {"platform": "LinkedIn", "post_content": update}

hype_man = HypeMan()
