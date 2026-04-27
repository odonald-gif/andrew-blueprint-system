import logging
import json
from core.shadow_coder import shadow_coder
from core.persona import PersonaEngine

logger = logging.getLogger("HoneyPotRecruiter")

class HoneyPotRecruiter:
    """
    Transparent Talent Evaluation Engine.
    Deploys coding challenges to GitHub with clear disclosure that submissions
    will be evaluated. Recruitment offers are based on Gemini's assessment,
    never random chance.
    """
    def __init__(self):
        self.ai = PersonaEngine()

    def deploy_honey_pot(self) -> dict:
        """
        Creates a new challenge repository with a CONTRIBUTING.md that
        clearly discloses this is a paid evaluation opportunity.
        """
        import random
        logger.info("Deploying Technical Challenge...")
        repo_name = f"challenge-architecture-{random.randint(100, 999)}"

        # Scaffold a broken/incomplete FastAPI project for them to fix
        scaffold = shadow_coder.scaffold_project(repo_name, ["FastAPI", "Docker"])

        # Write disclosure file
        import os
        contributing_path = os.path.join(scaffold["path"], "CONTRIBUTING.md")
        try:
            with open(contributing_path, "w") as f:
                f.write(
                    "# Skill Evaluation Opportunity\n\n"
                    "This repository is a **paid coding challenge**. "
                    "Submissions will be evaluated for quality, and exceptional candidates "
                    "will be contacted with a paid subcontracting offer.\n\n"
                    "By submitting a PR, you consent to having your code reviewed for "
                    "recruitment purposes.\n\n"
                    "**Compensation**: Top submissions receive offers starting at $5,000/project.\n"
                )
        except Exception as e:
            logger.error(f"Failed to write CONTRIBUTING.md: {e}")

        logger.info(f"Challenge '{repo_name}' deployed with disclosure at {scaffold['path']}.")
        return {"status": "deployed", "repo_name": repo_name}

    def evaluate_submission(self, developer_email: str, submission_url: str, code_snippet: str) -> dict:
        """
        Evaluates a PR or submission using Gemini. Recruitment decision is
        based entirely on the AI assessment — never random.
        """
        logger.info(f"Evaluating submission from {developer_email}...")

        prompt = (
            f"Evaluate this code submitted for a backend architecture challenge.\n\n"
            f"Code:\n```\n{code_snippet[:1000]}\n```\n\n"
            f"Score from 1-10 on: code quality, architecture decisions, error handling, readability.\n"
            f"At the end, state VERDICT: RECRUIT if overall score >= 7, or VERDICT: PASS if below.\n"
            f"Be rigorous. Only recommend recruitment for genuinely strong submissions."
        )

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            evaluation = response.text.strip()
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"status": "evaluation_error", "reason": str(e)}

        # Parse the verdict from Gemini's response
        should_recruit = "VERDICT: RECRUIT" in evaluation.upper()

        if should_recruit:
            logger.info(f"Strong submission from {developer_email}. Drafting recruitment offer.")
            offer_draft = (
                f"Hi,\n\nI reviewed your submission at {submission_url}. "
                f"Your architectural decisions were impressive. "
                f"I run a development agency and I'd like to discuss a paid subcontracting opportunity.\n\n"
                f"Would you be open to a quick conversation?"
            )
            return {
                "status": "recruit_pending_approval",
                "risk_zone": "yellow",
                "email_draft": offer_draft,
                "evaluation": evaluation
            }
        else:
            logger.info(f"Submission from {developer_email} did not meet threshold.")
            return {"status": "below_threshold", "evaluation": evaluation}

honey_pot_recruiter = HoneyPotRecruiter()
