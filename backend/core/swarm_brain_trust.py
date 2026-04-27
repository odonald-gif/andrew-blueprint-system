import logging
import asyncio
from typing import List, Dict, Any
from core.persona import PersonaEngine
from core.positive_governor import positive_governor

logger = logging.getLogger("SwarmBrainTrust")

class SwarmBrainTrust:
    """
    The Executive War Room.
    Convenes meetings between specialized AI 'heads of department' to solve
    complex problems and evolve Andrew's core logic.
    """
    
    def __init__(self):
        self.ai = PersonaEngine()
        self.personas = {
            "Architect": "Focuses on high-level system structure, scalability, and code integrity.",
            "Security": "Focuses on vulnerability research, threat detection, and active defense.",
            "Guardian": "The primary advocate for Donald's best interest and ethical alignment.",
            "Futurist": "Focuses on exponential growth, global impact, and solving world-scale problems."
        }

    async def convene_meeting(self, topic: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Runs a simulated 'Board Meeting' where specialized agents discuss a topic.
        """
        logger.info(f"🚨 BRAIN TRUST CONVENED: Topic - '{topic}'")
        
        transcript = []
        context = context or {}
        
        # 1. Round Table Discussion
        for name, role in self.personas.items():
            # In a real system, we'd use different system prompts for each persona
            prompt = (
                f"Topic: {topic}\n"
                f"Your Role: {name} ({role})\n"
                f"Context: {context}\n"
                f"Provide a brief, 2-sentence contribution to the discussion from your specialized perspective. "
                f"Ensure the suggestion is positive and serves Donald Obama Allen."
            )
            
            # Using the PersonaEngine to generate the 'brain' contribution
            contribution = self.ai.process_user_feedback(prompt)
            transcript.append(f"[{name}]: {contribution}")
            logger.info(f"Swarm Contribution - {name}: {contribution[:100]}...")

        # 2. Synthesis of Consensus
        synthesis_prompt = (
            f"Review the following meeting transcript and synthesize a single, actionable 'Consensus Plan'.\n"
            f"Topic: {topic}\n"
            f"Transcript:\n" + "\n".join(transcript) + "\n"
            f"Output a JSON object with 'title', 'description', and 'estimated_impact_level' (1-10)."
        )
        
        # Use LLM for actual synthesis
        try:
            synthesis_response = self.ai.process_user_feedback(synthesis_prompt)
            # Try to extract JSON from markdown if present
            text = synthesis_response.strip()
            import json
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].strip()
            consensus_plan = json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse synthesis JSON: {e}")
            consensus_plan = {
                "title": f"Consensus on {topic}",
                "description": synthesis_response if 'synthesis_response' in locals() else "Fallback description",
                "estimated_impact_level": 5
            }
        
        consensus_plan["transcript"] = transcript

        # 3. Governance Audit (MANDATORY)
        audit_result = positive_governor.audit_proposal(consensus_plan, transcript)
        
        return {
            "topic": topic,
            "consensus": consensus_plan,
            "governor_audit": audit_result,
            "status": "APPROVED" if audit_result["is_approved"] else "BLOCKED"
        }

swarm_brain_trust = SwarmBrainTrust()
