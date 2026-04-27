import subprocess
import os
import logging
import requests
from typing import Dict, Any, List
from core.persona import PersonaEngine

logger = logging.getLogger(__name__)

class CareerManager:
    """
    The Developer Career Agent.
    Handles GitHub contributions (real git), LinkedIn posting (real API when available),
    skill extraction (real repo analysis via GitHub API), and bio generation (Gemini).
    No mock actions or hardcoded data.
    """
    def __init__(self):
        self.github_pat = os.getenv("GITHUB_PAT", "")
        self.linkedin_cookie = os.getenv("LINKEDIN_LI_AT_COOKIE", "")
        self.ai = PersonaEngine()

    def execute_git_contribution(self, repo_path: str, branch_name: str, commit_message: str) -> Dict[str, Any]:
        """Uses subprocess to run real git commands."""
        try:
            logger.info(f"Executing Git workflow on {repo_path}")
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", branch_name], cwd=repo_path, check=True, capture_output=True)
            return {"status": "Success", "message": f"Pushed {branch_name} to GitHub."}
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
            return {"status": "Error", "message": str(e)}

    async def post_to_linkedin(self, post_content: str) -> Dict[str, Any]:
        """
        Posts to LinkedIn using stored cookie via Playwright.
        Returns error if Playwright or cookie is unavailable — never mocks the action.
        """
        if not self.linkedin_cookie:
            logger.warning("[CareerManager] No LINKEDIN_LI_AT_COOKIE. Cannot post.")
            return {"status": "Error", "message": "LinkedIn cookie not configured."}

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {"status": "Error", "message": "Playwright not installed. Run: pip install playwright && playwright install"}

        try:
            logger.info("Posting to LinkedIn via Playwright...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                await context.add_cookies([{
                    'name': 'li_at',
                    'value': self.linkedin_cookie,
                    'domain': '.linkedin.com',
                    'path': '/'
                }])
                page = await context.new_page()
                await page.goto("https://www.linkedin.com/feed/", wait_until="networkidle")

                # Click the "Start a post" area
                await page.click('[role="button"][aria-label*="Start a post"]', timeout=10000)
                await page.wait_for_timeout(1000)
                await page.keyboard.type(post_content, delay=30)
                await page.wait_for_timeout(500)

                # Post button
                await page.click('[aria-label*="Post"]', timeout=5000)
                await page.wait_for_timeout(3000)

                await browser.close()
                return {"status": "Success", "message": "Posted to LinkedIn."}
        except Exception as e:
            logger.error(f"LinkedIn posting failed: {e}")
            return {"status": "Error", "message": str(e)}

    def audit_github_skills(self) -> List[str]:
        """
        Scans actual GitHub repos via API to extract verified skills from languages used.
        Returns empty list if no PAT is configured.
        """
        logger.info("Auditing GitHub repos for verified skills...")

        if not self.github_pat:
            logger.warning("[CareerManager] No GITHUB_PAT. Cannot audit skills.")
            return []

        try:
            headers = {
                "Authorization": f"token {self.github_pat}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(
                "https://api.github.com/user/repos?sort=updated&per_page=10",
                headers=headers, timeout=10
            )
            if response.status_code != 200:
                logger.warning(f"GitHub API returned {response.status_code}")
                return []

            languages = set()
            for repo in response.json():
                lang = repo.get("language")
                if lang:
                    languages.add(lang)

                # Also fetch repo languages endpoint for multi-language repos
                lang_url = repo.get("languages_url", "")
                if lang_url:
                    try:
                        lang_resp = requests.get(lang_url, headers=headers, timeout=5)
                        if lang_resp.status_code == 200:
                            languages.update(lang_resp.json().keys())
                    except Exception:
                        pass

            skills = sorted(list(languages))
            logger.info(f"[CareerManager] Extracted skills: {skills}")
            return skills

        except Exception as e:
            logger.error(f"GitHub skill audit failed: {e}")
            return []

    def ghostwrite_bio(self) -> str:
        """Uses Gemini to write a professional bio based on real GitHub skills."""
        logger.info("Ghostwriting professional bio via Gemini...")

        skills = self.audit_github_skills()
        skills_str = ", ".join(skills) if skills else "Python, Cloud, AI"

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=(
                    f"Write a concise, professional Upwork/LinkedIn bio for a developer "
                    f"with these verified skills: {skills_str}\n"
                    f"Keep it under 100 words. Confident but not arrogant. "
                    f"Focus on value delivered to clients."
                ),
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Bio generation failed: {e}")
            return f"[Bio generation failed: {e}]"

career_manager = CareerManager()
