import logging
import os
from .persona import PersonaEngine

logger = logging.getLogger(__name__)

class UpworkEngine:
    """
    The Autonomous Earner.
    Scans Upwork via session cookie, drafts proposals via Gemini, queues for approval.
    No simulated job data — returns empty list when API is unavailable.
    """
    def __init__(self):
        self.session_cookie = os.getenv("UPWORK_SESSION_COOKIE", "")
        self.persona = PersonaEngine()

    def find_matching_jobs(self, skills: list) -> list:
        """
        Searches Upwork RSS feed for jobs matching the skill list.
        Returns empty list if no cookie or no matches — never fake data.
        """
        logger.info(f"Scanning Upwork for jobs matching: {skills}")

        if not self.session_cookie:
            logger.warning("[UpworkEngine] No UPWORK_SESSION_COOKIE set. Cannot scan.")
            return []

        # Use Upwork's public RSS feed for job search (no auth required for reading)
        import requests
        try:
            query = "+".join(skills[:3])
            url = f"https://www.upwork.com/ab/feed/jobs/rss?q={query}&sort=recency"
            response = requests.get(url, timeout=15, headers={"User-Agent": "Andrew/1.0"})

            if response.status_code != 200:
                logger.warning(f"[UpworkEngine] RSS feed returned {response.status_code}")
                return []

            # Parse RSS XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            jobs = []
            for item in root.findall(".//item")[:5]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                description = item.findtext("description", "")[:200]
                jobs.append({
                    "title": title,
                    "url": link,
                    "description": description,
                    "source": "upwork_rss"
                })

            logger.info(f"[UpworkEngine] Found {len(jobs)} jobs from RSS feed.")
            return jobs

        except Exception as e:
            logger.error(f"[UpworkEngine] Job scan failed: {e}")
            return []

    def push_resume_and_bid(self, job: dict) -> dict:
        """
        Drafts a proposal using Gemini in Donald's voice.
        Queued in Yellow Zone for approval — never sent automatically.
        """
        logger.info(f"Drafting bid for: {job.get('title', 'unknown')}...")

        try:
            response = self.persona.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=(
                    f"Write a short, professional Upwork proposal for this job:\n"
                    f"Title: {job.get('title', '')}\n"
                    f"Description: {job.get('description', '')}\n\n"
                    f"Write as a confident IT professional. Keep it under 150 words. "
                    f"Mention relevant skills and availability."
                ),
            )
            cover_letter = response.text.strip()
        except Exception as e:
            logger.error(f"Proposal generation failed: {e}")
            cover_letter = f"[Draft generation failed: {e}]"

        return {
            "title": job.get("title", ""),
            "url": job.get("url", ""),
            "cover_letter_draft": cover_letter,
            "action": "PENDING_APPROVAL"
        }

    def take_the_work(self, job_id: str) -> bool:
        """
        Logs acceptance intent. Actual Upwork contract acceptance
        requires manual action — Andrew drafts, you confirm.
        """
        logger.info(f"[UpworkEngine] Job {job_id} marked as accepted. Manual confirmation needed on Upwork.")
        return True

upwork_engine = UpworkEngine()
