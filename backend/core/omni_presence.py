import os
import logging
from core.persona import PersonaEngine
from core.api_pool import api_pool

logger = logging.getLogger("OmniPresence")

class OmniPresence:
    """
    Organic Traffic & Lead Generation Engine.
    Uses Gemini to identify high-value technical questions in target niches,
    drafts expert answers, and queues them for user review.
    """
    def __init__(self):
        self.ai = PersonaEngine()
        self.portfolio_url = os.getenv("PORTFOLIO_URL", "")
        self.niche_keywords = ["FastAPI deployment", "Oracle Cloud ARM", "AI agent framework", "n8n automation"]

    def scan_forums(self) -> list:
        """
        Scans for high-value technical questions using Gemini research.
        Returns a list of drafted replies ready for user review.
        Called by agent_runtime.py during the 'researching' sense cycle.
        """
        logger.info(f"Scanning for high-value technical queries in {self.niche_keywords}...")

        account = api_pool.acquire("gemini_calls", preferred_role="scout")
        if account is None:
            logger.warning("[OmniPresence] No Gemini quota available for forum scan.")
            return []

        niches = ", ".join(self.niche_keywords)
        prompt = (
            f"You are a senior developer who monitors Reddit, StackOverflow, and GitHub Discussions. "
            f"Identify 3 realistic technical questions that people are currently struggling with in these niches: {niches}. "
            f"For each question, provide:\n"
            f"1. Platform (Reddit/StackOverflow/GitHub)\n"
            f"2. The question title\n"
            f"3. A brief 1-line description of the problem\n"
            f"4. A concise, expert-level answer (3-5 sentences max)\n\n"
            f"Return as a JSON array of objects with keys: platform, title, problem, answer.\n"
            f"Return only the JSON, no markdown blocks."
        )

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            import json
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```json")[-1].split("```")[0].strip() if "```json" in text else text.split("```")[1].strip()
            questions = json.loads(text)
        except Exception as e:
            logger.error(f"OmniPresence scan failed: {e}")
            return []

        results = []
        for q in questions:
            answer = q.get("answer", "")

            # Append portfolio link only if configured — no broken URLs
            if self.portfolio_url:
                answer += f"\n\nI've open-sourced some tooling for this at {self.portfolio_url}"

            results.append({
                "status": "draft_ready",
                "risk_zone": "yellow",
                "platform": q.get("platform", "Unknown"),
                "question": q.get("title", ""),
                "problem": q.get("problem", ""),
                "reply_draft": answer
            })

        logger.info(f"OmniPresence generated {len(results)} reply drafts.")
        return results

    def execute_scan_and_reply(self) -> dict:
        """
        Legacy method — wraps scan_forums() for backward compatibility.
        Returns the first result or an empty status.
        """
        results = self.scan_forums()
        if results:
            return results[0]
        return {"status": "no_results", "risk_zone": "green"}

omnipresence = OmniPresence()
