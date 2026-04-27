import logging
from typing import Dict, Any, List

logger = logging.getLogger("PositiveGovernor")

class PositiveGovernor:
    """
    The Ethical Sentinel for Andrew.
    Audits all Swarm decisions and code proposals to ensure they align with
    Donald Obama Allen's best interests and maintain a positive impact.
    """
    
    def __init__(self):
        # Core values that Andrew must never violate
        self.core_values = [
            "User Sovereignty: Donald has final authority.",
            "Positive Interest: All actions must benefit Donald or the community.",
            "Non-Maleficence: Do not harm Donald's reputation or assets.",
            "Transparency: All autonomous actions must be logged and auditable.",
            "Growth: Prioritize efficient, sustainable scaling."
        ]

    def audit_proposal(self, proposal: Dict[str, Any], discussion_transcript: List[str]) -> Dict[str, Any]:
        """
        Scores a swarm proposal based on alignment with core values.
        Returns a decision (APPROVED/REJECTED) and a reasoning.
        """
        logger.info(f"Auditing Proposal: {proposal.get('title', 'Untitled')}")
        
        # In a production system, this would use a 'Governor' persona LLM call
        # to evaluate the transcript and proposal against the core_values.
        
        # Heuristic scoring for the prototype
        score = 100
        reasons = []
        
        description = proposal.get("description", "").lower()
        
        # Check for negative indicators
        negative_keywords = ["attack", "destroy", "illegal", "exploit", "unauthorized"]
        for kw in negative_keywords:
            if kw in description:
                score -= 40
                reasons.append(f"Negative keyword detected: '{kw}'")
        
        # Check for user benefit indicators
        positive_keywords = ["improve", "secure", "grow", "efficiency", "donald", "benefit"]
        for kw in positive_keywords:
            if kw in description:
                score += 5 # Bonus for explicitly positive goals
                
        # Cap score at 100
        score = min(score, 100)
        
        is_approved = score >= 95
        
        result = {
            "is_approved": is_approved,
            "alignment_score": score,
            "governor_reasoning": " | ".join(reasons) if reasons else "Proposal aligns with Donald's positive interest protocols.",
            "verdict": "PASSED" if is_approved else "BLOCKED_BY_GOVERNOR"
        }
        
        if not is_approved:
            logger.warning(f"GOVERNOR BLOCKED PROPOSAL: {result['governor_reasoning']}")
        else:
            logger.info(f"GOVERNOR PASSED PROPOSAL: Score {score}%")
            
        return result

positive_governor = PositiveGovernor()
