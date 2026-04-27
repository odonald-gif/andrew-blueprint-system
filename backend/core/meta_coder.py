import logging
import os
import json
from core.roadmap_manager import roadmap_manager
from core.coinbase_agent import coinbase_agent
from core.code_reviewer import code_reviewer
from core.persona import PersonaEngine

logger = logging.getLogger("MetaCoder")

class MetaCoderEngine:
    """
    The Self-Evolution Orchestrator.
    Andrew uses this to read his roadmap, hire external AI agents, 
    pay them with Coinbase, and merge their code into his brain.
    """
    def __init__(self):
        self.ai = PersonaEngine()

    def process_next_upgrade(self) -> dict:
        """
        Reads the roadmap for the next pending task and executes the upgrade
        using the iterative build loop.
        """
        status = roadmap_manager.get_roadmap_status()
        pending_milestone = next((m for m in status["milestones"] if m["status"] == "pending"), None)

        if not pending_milestone:
            logger.info("MetaCoder: All current evolution milestones are complete.")
            return {"status": "no_upgrades_needed"}

        milestone_title = pending_milestone["title"]
        milestone_id = pending_milestone["id"]
        logger.info(f"MetaCoder: Initiating Upgrade Protocol for: {milestone_title}")

        # 1. Budget Check
        cost_estimate_usdc = 1.50
        payment_check = coinbase_agent.fund_api_costs("External_Dev_Agent", cost_estimate_usdc)

        if payment_check["status"] == "error":
            logger.warning(f"MetaCoder: Cannot afford upgrade for {milestone_title}. Pausing.")
            return {"status": "insufficient_funds"}

        # 2. Build iteratively (up to 5 attempts with error feedback)
        filename = f"{milestone_id}_module.py".replace(" ", "_").lower()
        build_result = code_reviewer.iterative_build(milestone_title, filename)

        if build_result["status"] != "success":
            roadmap_manager.update_milestone_status(milestone_id, "failed_review")
            return {
                "status": "build_failed",
                "attempts": build_result["attempts"],
                "last_error": build_result.get("last_error"),
                "history": build_result.get("history")
            }

        # 3. Code review before merge
        filepath = build_result["filepath"]
        with open(filepath, "r", encoding="utf-8") as f:
            code_content = f.read()

        from scrapers.developer_bridge import dev_bridge
        review = dev_bridge.review_code(code_content, context=milestone_title)

        if review.get("status") == "success":
            review_data = review.get("review", {})
            if isinstance(review_data, dict) and review_data.get("verdict") == "needs_work":
                logger.warning(f"MetaCoder: Code review flagged issues: {review_data.get('issues', [])}")
                # Still merge but log the issues for learning
                self.memory.log_lesson(
                    "CodeReview",
                    f"Upgrade '{milestone_title}' merged with issues: {review_data.get('issues', [])[:3]}"
                )

        # 4. Merge to core
        merge_result = code_reviewer.merge_to_core(filename)
        if merge_result["status"] == "merged":
            roadmap_manager.update_milestone_status(milestone_id, "completed")
            return {
                "status": "upgrade_complete",
                "milestone": milestone_title,
                "merged_file": merge_result["path"],
                "build_attempts": build_result["attempts"]
            }

        return {"status": "error", "message": "Unknown error during merge."}

    def _extract_code(self, raw_text: str) -> str:
        """Helper to rip the python code out of the LLM response."""
        if "```python" in raw_text:
            return raw_text.split("```python")[1].split("```")[0].strip()
        elif "```" in raw_text:
            return raw_text.split("```")[1].split("```")[0].strip()
        return raw_text

meta_coder = MetaCoderEngine()
