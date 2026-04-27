import logging
import datetime
from core.black_book import BlackBook
from core.persona import PersonaEngine

logger = logging.getLogger("RelationshipDrip")

class RelationshipDrip:
    """
    Drip Relationship Management Engine (The 'Long Game').
    Scans the Black Book for high-value contacts that haven't been contacted recently,
    and drafts casual, highly personalized check-in messages.
    """
    def __init__(self):
        self.memory = BlackBook()
        self.ai = PersonaEngine()

    def generate_drips(self) -> list:
        """
        Query the DB for profiles and draft check-in messages.
        """
        logger.info("Scanning Black Book for stagnant high-value relationships...")
        
        profiles = self.memory.execute_query(
            "SELECT name, priority_level, notes FROM Profiles WHERE priority_level >= 4 ORDER BY priority_level DESC LIMIT 5"
        )
        
        if not profiles:
            return []
            
        drips = []
        for profile in profiles:
            name, priority_level, notes = profile
            
            stagnant_contact = {
                "name": name,
                "priority_level": priority_level,
                "notes": notes
            }
            
            # Prompt the persona to generate a natural, non-spammy check-in
            prompt = f"Draft a short, casual text message to {name}. Context: {notes}. Just checking in, maybe asking how their latest product launch went."
            
            draft_msg = self.ai.process_user_feedback(prompt)
            
            logger.info(f"Drafted Relationship Drip for {name}")
            
            drips.append({
                "contact": name,
                "status": "draft_ready",
                "message": draft_msg
            })
        
        return drips

relationship_drip = RelationshipDrip()
