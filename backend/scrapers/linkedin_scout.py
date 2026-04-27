import os
import logging
import requests
from typing import Dict, List, Any
from core.persona import PersonaEngine

logger = logging.getLogger(__name__)

class LinkedInScout:
    """
    The Professional Emissary.
    Uses LinkedIn's public job search (no auth) and Gemini for content drafting.
    No simulated payloads — returns empty when nothing is found.
    """
    def __init__(self):
        self.target_keywords = ["Cloud Architecture", "DevOps Intern", "AI Engineer Junior"]
        self.location = "Remote"
        self.ai = PersonaEngine()

    def scan_for_opportunities(self) -> List[Dict[str, Any]]:
        """
        Searches for job opportunities using Google search targeting LinkedIn.
        Returns real results or empty list — never simulated data.
        """
        logger.info(f"Scanning for LinkedIn opportunities: {self.target_keywords}...")

        try:
            # Use Google Custom Search API if available, else return empty
            google_key = os.getenv("GOOGLE_CLOUD_KEY_1")  # scout account
            search_cx = os.getenv("GOOGLE_SEARCH_CX", "")

            if not google_key or not search_cx:
                logger.info("[LinkedInScout] No Google Search API configured. Skipping scan.")
                return []

            query = f"site:linkedin.com/jobs {' OR '.join(self.target_keywords)} {self.location}"
            url = f"https://www.googleapis.com/customsearch/v1?key={google_key}&cx={search_cx}&q={query}"

            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                logger.warning(f"[LinkedInScout] Search API returned {response.status_code}")
                return []

            data = response.json()
            results = []
            for item in data.get("items", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "linkedin_via_google"
                })

            logger.info(f"[LinkedInScout] Found {len(results)} opportunities.")
            return results

        except Exception as e:
            logger.error(f"[LinkedInScout] Scan failed: {e}")
            return []

    def draft_milestone_post(self, skill_learned: str) -> str:
        """
        Uses Gemini to draft a LinkedIn post when a new skill is mastered.
        """
        logger.info(f"Drafting LinkedIn post for: {skill_learned}")
        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=(
                    f"Write a short, professional LinkedIn post (under 100 words) "
                    f"about mastering: {skill_learned}\n"
                    f"Tone: Confident but humble. Include 2-3 relevant hashtags."
                ),
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Post drafting failed: {e}")
            return f"[Draft failed: {e}]"

linkedin_scout = LinkedInScout()
