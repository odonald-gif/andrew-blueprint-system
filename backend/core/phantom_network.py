import os
import logging
from core.shadow_coder import shadow_coder
from core.reputation_builder import reputation_builder
from core.persona import PersonaEngine
from core.api_pool import api_pool

logger = logging.getLogger("PhantomNetwork")

class PhantomNetwork:
    """
    Proactive B2B Lead Generation Engine.
    Scans for businesses with poor web infrastructure using real search,
    builds them a free landing page, and drafts an outreach email for
    user approval.
    """
    def __init__(self):
        self.ai = PersonaEngine()
        self.portfolio_url = os.getenv("PORTFOLIO_URL", "")

    def scan_and_deploy(self) -> dict:
        """
        Uses Gemini to identify a plausible local business lead,
        scaffolds a solution, and drafts an outreach email.
        All drafts are queued for user approval — nothing sends automatically.
        """
        logger.info("Initiating Phantom Network lead generation scan...")

        account = api_pool.acquire("gemini_calls", preferred_role="scout")
        if account is None:
            return {"status": "no_quota"}

        # Step 1: Use Gemini to research a real business niche with web issues
        try:
            prompt = (
                "You are a B2B lead research analyst. Identify ONE specific type of local business "
                "(e.g., plumbers, dentists, florists) that commonly has slow, outdated websites. "
                "Return a JSON object with: "
                '{"business_type": "...", "common_issue": "...", "outreach_angle": "..."}'
                "\nReturn only the JSON, no markdown."
            )
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            import json
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```json")[-1].split("```")[0].strip() if "```json" in text else text.split("```")[1].strip()
            target = json.loads(text)
        except Exception as e:
            logger.error(f"Phantom Network research failed: {e}")
            return {"status": "research_error", "reason": str(e)}

        business_type = target.get("business_type", "local business")
        common_issue = target.get("common_issue", "slow website")
        outreach_angle = target.get("outreach_angle", "performance optimization")

        # Step 2: Scaffold a demo project
        project_name = f"{business_type.lower().replace(' ', '-')}-fast-site"
        scaffold_result = shadow_coder.scaffold_project(project_name, ["React"])

        # Step 3: Draft outreach email using reputation builder
        email_draft = reputation_builder.draft_cold_outreach(
            company_name=f"[Target {business_type.title()}]",
            target_person="[Owner Name]",
            detected_issue=common_issue
        )

        # Add portfolio link only if configured
        if self.portfolio_url:
            email_draft["body"] += f"\n\nYou can see examples of my work here: {self.portfolio_url}"

        logger.info("Phantom Network draft ready for user review.")

        return {
            "status": "ready_for_review",
            "risk_zone": "yellow",
            "business_type": business_type,
            "outreach_angle": outreach_angle,
            "scaffolded_path": scaffold_result["path"],
            "email_draft": email_draft["body"]
        }

phantom_network = PhantomNetwork()
