import logging
from typing import Dict, Any
import os
import sys

# Ensure backend module can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    from backend.core.persona import PersonaEngine
except ImportError:
    PersonaEngine = None

logger = logging.getLogger(__name__)

class ProposalCloser:
    """
    The 'Sales' arm of Andrew. Analyzes job postings from the Scout
    and drafts highly targeted proposals leveraging the User's GitHub portfolio.
    """
    def __init__(self):
        self.persona = PersonaEngine() if PersonaEngine else None

    def _get_github_portfolio_summary(self) -> str:
        """
        Fetches real top repositories from GitHub API to build the portfolio summary.
        Falls back to known projects if API is unavailable.
        """
        github_username = os.getenv("GITHUB_USERNAME", "")
        if not github_username:
            logger.warning("GITHUB_USERNAME not set. Using known project list.")
            return self._get_known_portfolio()

        try:
            import requests
            resp = requests.get(
                f"https://api.github.com/users/{github_username}/repos",
                params={"sort": "updated", "per_page": 5, "type": "owner"},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            if resp.status_code == 200:
                repos = resp.json()
                lines = []
                for repo in repos:
                    desc = repo.get("description", "No description")
                    lang = repo.get("language", "Unknown")
                    stars = repo.get("stargazers_count", 0)
                    lines.append(f"- {repo['name']} ({lang}, ⭐{stars}): {desc}")
                if lines:
                    return "\n".join(lines)
            logger.warning(f"GitHub API returned {resp.status_code}. Using known portfolio.")
        except Exception as e:
            logger.warning(f"GitHub API error: {e}. Using known portfolio.")

        return self._get_known_portfolio()

    def _get_known_portfolio(self) -> str:
        """Fallback portfolio from known projects."""
        return (
            "- Built 'Project Andrew', an autonomous Executive Twin in Python/FastAPI.\n"
            "- Built 'Patient Identity Service' using event-driven architectures.\n"
            "- Strong background in React, Flutter UI, and DevOps (Oracle/Docker)."
        )

    def draft_proposal(self, job_title: str, job_description: str) -> Dict[str, Any]:
        """
        Uses the Persona Engine to draft a high-conversion proposal.
        PersonaEngine already requires GEMINI_API_KEY — no mock fallback.
        """
        logger.info(f"Closer: Drafting proposal for '{job_title}'")

        if not self.persona:
            raise RuntimeError("Closer cannot operate without PersonaEngine. Ensure GEMINI_API_KEY is set.")

        portfolio = self._get_github_portfolio_summary()

        prompt = (
            f"You are the user, an elite Senior Systems Architect. Draft a very concise, "
            f"high-conversion Upwork proposal for the following job:\n\n"
            f"Title: {job_title}\n"
            f"Description: {job_description}\n\n"
            f"Leverage this portfolio experience to prove competence:\n{portfolio}\n\n"
            f"Do not sound desperate. Sound like a peer offering a technical solution. "
            f"End with a call to action for a 10-minute technical sync."
        )

        try:
            response = self.persona.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=self.persona.system_prompt + "\n\n" + prompt,
            )
            draft = response.text.strip()
            return {"status": "success", "proposal": draft}
        except Exception as e:
            logger.error(f"Closer API Error: {e}")
            raise RuntimeError(f"Closer failed to draft proposal: {e}")

closer = ProposalCloser()
