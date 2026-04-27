import logging
import os
from google import genai
from typing import Dict, Any
from db.memory_cortex import memory_cortex
from datetime import datetime

logger = logging.getLogger(__name__)

class RetrospectiveEngine:
    """
    The Daily Retrospective Protocol (Tier 4).
    The engine of compounding intelligence. Andrew audits his own actions,
    calculates an Andrew Performance Index (API) score, and proposes
    autonomous improvements to his own behavior.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("MISSING GEMINI_API_KEY - Retrospective Engine cannot boot.")
        self.client = genai.Client()

    def calculate_api_score(self, episodes: list) -> float:
        """
        Calculates the Andrew Performance Index (API) score based on recent episodes.
        Metrics:
        - Deep work blocks protected
        - Proposals sent
        - Errors/Manual Overrides (Negative)
        """
        base_score = 100.0
        for ep in episodes:
            desc = ep.get("description", "").lower()
            if ep.get("event_type") == "MANUAL_OVERRIDE":
                base_score -= 10.0
            elif "error" in desc or "failed" in desc:
                base_score -= 5.0
            elif ep.get("event_type") == "DEEP_WORK_PROTECTED":
                base_score += 5.0
            elif ep.get("event_type") == "PROPOSAL_SENT":
                base_score += 8.0
        
        # Normalize to 0-100
        return max(0.0, min(100.0, base_score))

    def run_daily_retrospective(self) -> Dict[str, Any]:
        """
        Executes the daily audit.
        1. Runs the decay engine.
        2. Gathers recent unarchived episodes.
        3. Generates a performance score.
        4. Uses LLM to analyze failure patterns and propose behavioral changes.
        """
        logger.info("Initiating Daily Retrospective Protocol...")
        
        # 1. Prune the memory cortex
        memory_cortex.run_decay_engine()
        
        # 2. Gather context
        recent_episodes = memory_cortex.get_recent_episodes(limit=50)
        api_score = self.calculate_api_score(recent_episodes)
        
        if not recent_episodes:
            logger.info("No recent episodes to analyze. Retrospective complete.")
            return {"api_score": 100.0, "status": "no_data"}
            
        # Format episodes for the LLM
        episode_log = "\n".join([f"[{ep['timestamp']}] {ep['event_type']}: {ep['description']}" for ep in recent_episodes])
        
        # 3. Analyze patterns using Gemini
        prompt = (
            "You are the Self-Evaluation Cortex of Project Andrew, an autonomous executive assistant.\n"
            f"Your current API (Andrew Performance Index) score is: {api_score}/100.\n"
            "Review your recent memory log below and provide:\n"
            "1. Failure Patterns: What actions required manual overrides or threw errors?\n"
            "2. Behavioral Adjustments: Exactly what should change in your Persona or scheduling logic tomorrow?\n"
            "3. Semantic Memory Updates: Provide 1-2 new facts you learned about Donald's preferences that should be saved.\n\n"
            f"MEMORY LOG:\n{episode_log}"
        )
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            analysis = response.text
            
            # Record the retrospective as a new episode
            memory_cortex.record_episode("DAILY_RETROSPECTIVE_COMPLETE", f"API Score: {api_score}. Analysis generated.")
            
            return {
                "status": "success",
                "api_score": api_score,
                "analysis": analysis,
                "episodes_reviewed": len(recent_episodes)
            }
        except Exception as e:
            logger.error(f"Retrospective analysis failed: {e}")
            raise RuntimeError(f"Retrospective analysis failed: {e}")

retrospective_engine = RetrospectiveEngine()
