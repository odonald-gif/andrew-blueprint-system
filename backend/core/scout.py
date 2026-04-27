import logging
import os
import requests
from core.persona import PersonaEngine
from core.google_search import google_search

logger = logging.getLogger(__name__)

class ScoutEngine:
    """
    The Relocation Engine & Opportunity Scout.
    Searches for real scholarships, internships, and hackathons via
    Google Custom Search and GitHub APIs.
    Never returns hardcoded opportunity data.
    """
    def __init__(self):
        self.ai = PersonaEngine()

    def calculate_win_probability(self, event_description: str, user_skills: list) -> float:
        """
        Uses Gemini to estimate win probability based on the user's skills
        vs. the event requirements. Returns 0.0-1.0.
        """
        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=(
                    f"Given a developer with these skills: {', '.join(user_skills)}\n"
                    f"Estimate the probability (0.0 to 1.0) of winning/placing in: {event_description}\n"
                    f"Return ONLY a decimal number, nothing else."
                ),
            )
            text = response.text.strip()
            return min(1.0, max(0.0, float(text)))
        except Exception as e:
            logger.warning(f"Win probability estimation failed: {e}")
            return 0.5  # Unknown = 50%

    def scan_opportunities(self) -> dict:
        """
        Searches for real opportunities using Google Custom Search and GitHub.
        Returns structured results or empty status when nothing is found.
        """
        logger.info("Scouting for relocation and opportunity leads...")

        results = {
            "internships": [],
            "scholarships": [],
            "hackathons": [],
            "action_items": []
        }

        # 1. Google Custom Search for scholarships
        scholarship_search = google_search.search_recent(
            query="fully funded masters scholarship computer science 2026 applications open",
            days=30,
            num_results=5,
        )
        if scholarship_search["status"] == "success":
            for item in scholarship_search["results"]:
                results["scholarships"].append({
                    "program": item["title"],
                    "url": item["link"],
                    "description": item["snippet"],
                    "source": item["source"],
                })

        # 2. Google Custom Search for internships
        internship_search = google_search.search_recent(
            query="remote software engineering internship 2026 paid",
            days=30,
            num_results=5,
        )
        if internship_search["status"] == "success":
            for item in internship_search["results"]:
                results["internships"].append({
                    "title": item["title"],
                    "url": item["link"],
                    "description": item["snippet"],
                    "source": item["source"],
                })

        # 3. Google Custom Search for hackathons with prizes
        hackathon_search = google_search.search_recent(
            query="online hackathon 2026 prize money AI developer",
            days=30,
            num_results=5,
        )
        if hackathon_search["status"] == "success":
            for item in hackathon_search["results"]:
                results["hackathons"].append({
                    "name": item["title"],
                    "url": item["link"],
                    "description": item["snippet"],
                    "source": item["source"],
                })

        # 4. Supplement with GitHub hackathon repos (existing logic)
        try:
            github_pat = os.getenv("GITHUB_PAT", "")
            headers = {"Accept": "application/vnd.github.v3+json"}
            if github_pat:
                headers["Authorization"] = f"token {github_pat}"

            response = requests.get(
                "https://api.github.com/search/repositories?q=hackathon+2026&sort=updated&per_page=3",
                headers=headers, timeout=10
            )
            if response.status_code == 200:
                for repo in response.json().get("items", []):
                    results["hackathons"].append({
                        "name": repo.get("name", ""),
                        "url": repo.get("html_url", ""),
                        "description": (repo.get("description") or "")[:100],
                        "stars": repo.get("stargazers_count", 0),
                        "source": "github.com",
                    })
        except Exception as e:
            logger.warning(f"Hackathon scan failed: {e}")

        # 5. Use Gemini to suggest action items based on findings
        if any(results.values()):
            try:
                response = self.ai.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=(
                        f"Based on these opportunities found: {results}\n"
                        f"Suggest 1-2 concrete action items. Be specific and brief."
                    ),
                )
                results["action_items"] = [response.text.strip()]
            except Exception:
                pass

        return results

scout_engine = ScoutEngine()

