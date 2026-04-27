import logging
from core.persona import PersonaEngine

logger = logging.getLogger("LegalFirewall")

class LegalFirewall:
    """
    Automated Contract Redlining Engine.
    Scans incoming NDAs or freelance agreements for predatory clauses
    and generates professional counter-offers.
    """
    def __init__(self):
        self.ai = PersonaEngine()

    def analyze_contract(self, client_name: str, contract_text: str) -> dict:
        """
        Parses contract text to flag unlimited revisions, IP surrender, or Net-90 terms.
        """
        logger.info(f"Legal Firewall scanning contract from {client_name}...")
        
        # In production, we pass the full text. Here we use the AI to analyze it.
        prompt = f"""
        You are Andrew, a highly protective legal and executive assistant for Donald Allen.
        Analyze the following freelance contract excerpt. Flag any predatory clauses 
        (e.g., unlimited revisions, IP surrendered before full payment, payment terms > Net-30).
        Then, draft a professional but firm counter-offer email to the client addressing these issues.
        
        Contract excerpt: "{contract_text[:1000]}"
        """
        
        analysis = self.ai.process_user_feedback(prompt)
        
        logger.info(f"Contract analysis complete for {client_name}. Flagged potential risks.")
        
        return {
            "status": "analysis_complete",
            "client": client_name,
            "redline_report": analysis
        }

legal_firewall = LegalFirewall()
