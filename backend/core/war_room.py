import logging
from core.black_book import BlackBook

logger = logging.getLogger("WarRoom")

class WarRoom:
    """
    Predictive Negotiation Engine.
    Generates a 3-bullet cheat sheet before meetings based on Black Book data.
    """
    def __init__(self):
        self.memory = BlackBook()

    def generate_cheat_sheet(self, contact_name: str) -> dict:
        """Pulls intel on the contact and outputs negotiation angles."""
        logger.info(f"War Room activated for contact: {contact_name}")
        
        profile = self.memory.get_profile(contact_name)
        
        if not profile:
            return {
                "contact": contact_name,
                "status": "no_data",
                "cheat_sheet": [
                    "No prior data. Play it safe and ask probing questions.",
                    "Identify their core pain point in the first 5 minutes.",
                    "Do not commit to pricing until scope is fully defined."
                ]
            }

        notes = profile.get("notes", "")
        try:
            from core.persona import persona_engine
            prompt = f"Analyze the following CRM notes for {contact_name} and generate exactly 3 punchy negotiation tactics as bullet points. Notes: {notes}"
            response = persona_engine.process_user_feedback(prompt)
            tactics = [line.strip().lstrip('- ') for line in response.split('\\n') if line.strip()][:3]
            if not tactics:
                tactics = ["No specific tactics extracted.", "Play it safe.", f"Priority Level: {profile.get('priority_level')}"]
        except Exception as e:
            logger.error(f"Failed to generate tactics via PersonaEngine: {e}")
            raise RuntimeError(f"WarRoom LLM failure: {e}. Andrew, use Developer Bridge to fix the integration.")

        return {
            "contact": contact_name,
            "status": "intel_retrieved",
            "cheat_sheet": tactics
        }

war_room = WarRoom()
