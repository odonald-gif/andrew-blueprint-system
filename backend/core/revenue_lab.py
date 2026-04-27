"""
Revenue Lab: Andrew's Parallel Experiment Engine.

Andrew doesn't bet everything on one revenue stream.
He runs multiple experiments simultaneously, tracks what converts,
and doubles down on what works — autonomously.

Each experiment is a lightweight trial with a defined hypothesis,
a measurable success metric, and a TTL (days until verdict).
"""

import json
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from core.black_book import BlackBook
from core.persona import PersonaEngine
from core.api_pool import api_pool

logger = logging.getLogger(__name__)

# Andrew's current active experiment tracks.
# Add new ones as the market evolves.
EXPERIMENT_TEMPLATES = [
    {
        "id": "upwork_outreach",
        "name": "Upwork Proposal Blitz",
        "hypothesis": "Sending 10 tailored proposals/day will land 1 paid client within 14 days.",
        "success_metric": "paid_contract_signed",
        "ttl_days": 14,
        "risk_zone": "yellow",
    },
    {
        "id": "cold_email_b2b",
        "name": "B2B Cold Email — AI Automation",
        "hypothesis": "50 personalised cold emails/day to SMB owners will generate 3+ discovery calls/week.",
        "success_metric": "discovery_call_booked",
        "ttl_days": 21,
        "risk_zone": "yellow",
    },
    {
        "id": "content_seo",
        "name": "Long-Form SEO Content",
        "hypothesis": "Publishing 3 authoritative AI automation articles/week will generate inbound leads within 60 days.",
        "success_metric": "inbound_lead_received",
        "ttl_days": 60,
        "risk_zone": "green",
    },
    {
        "id": "github_leads",
        "name": "GitHub Developer Lead Mining",
        "hypothesis": "Reaching out to open-source project maintainers needing automation will convert 1 in 20.",
        "success_metric": "paid_contract_signed",
        "ttl_days": 30,
        "risk_zone": "yellow",
    },
]


class RevenueLab:
    """
    Manages Andrew's portfolio of revenue experiments.
    Each experiment runs in parallel, is time-boxed, and produces
    a clear winner/loser verdict that Andrew learns from.
    """

    def __init__(self):
        self.memory = BlackBook()
        self.ai = PersonaEngine()
        self._ensure_table()

    def _ensure_table(self):
        self.memory.execute_query("""
            CREATE TABLE IF NOT EXISTS RevenueExperiments (
                id            TEXT    PRIMARY KEY,
                name          TEXT    NOT NULL,
                hypothesis    TEXT,
                success_metric TEXT,
                status        TEXT    DEFAULT 'active',
                started_date  TEXT,
                ttl_days      INTEGER DEFAULT 14,
                results       TEXT    DEFAULT '{}',
                verdict       TEXT,
                updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # ── Lifecycle ────────────────────────────────────────────────

    def seed_experiments(self):
        """Seed the default experiments if they haven't been started yet."""
        for tmpl in EXPERIMENT_TEMPLATES:
            existing = self.memory.execute_query(
                "SELECT id FROM RevenueExperiments WHERE id = ?", (tmpl["id"],)
            )
            if not existing:
                self.memory.execute_query(
                    """INSERT INTO RevenueExperiments (id, name, hypothesis, success_metric, started_date, ttl_days)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (tmpl["id"], tmpl["name"], tmpl["hypothesis"],
                     tmpl["success_metric"], str(date.today()), tmpl["ttl_days"])
                )
                logger.info(f"[RevenueLab] Started experiment: {tmpl['name']}")

    def log_result(self, experiment_id: str, metric: str, value: Any):
        """Record a data point for an experiment (e.g., emails_sent=50, replies=3)."""
        rows = self.memory.execute_query(
            "SELECT results FROM RevenueExperiments WHERE id = ?", (experiment_id,)
        )
        if not rows:
            logger.warning(f"[RevenueLab] Unknown experiment: {experiment_id}")
            return

        results = json.loads(rows[0][0] or "{}")
        results[metric] = results.get(metric, 0) + (value if isinstance(value, (int, float)) else 1)

        self.memory.execute_query(
            "UPDATE RevenueExperiments SET results=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(results), experiment_id)
        )
        logger.info(f"[RevenueLab] {experiment_id}: {metric} = {results[metric]}")

    def evaluate_experiments(self) -> List[Dict[str, Any]]:
        """
        Review all active experiments. For any past their TTL,
        ask Gemini to deliver a verdict and extract the lesson.
        Returns a list of verdicts.
        """
        today = date.today()
        rows = self.memory.execute_query(
            "SELECT id, name, hypothesis, success_metric, started_date, ttl_days, results FROM RevenueExperiments WHERE status='active'"
        )

        verdicts = []
        for exp_id, name, hypothesis, metric, started, ttl, results_json in rows:
            start_date = date.fromisoformat(started)
            age_days = (today - start_date).days

            if age_days < ttl:
                continue  # Still running, not time for verdict

            results = json.loads(results_json or "{}")
            verdict = self._request_verdict(name, hypothesis, metric, results, age_days)

            self.memory.execute_query(
                "UPDATE RevenueExperiments SET status='complete', verdict=? WHERE id=?",
                (verdict, exp_id)
            )
            self.memory.log_lesson(
                context=f"revenue_experiment:{exp_id}",
                lesson=verdict
            )
            verdicts.append({"experiment": name, "verdict": verdict})
            logger.info(f"[RevenueLab] Verdict for '{name}': {verdict[:60]}...")

        return verdicts

    def get_active_summary(self) -> List[Dict[str, Any]]:
        """Quick status of all running experiments."""
        rows = self.memory.execute_query(
            "SELECT id, name, status, started_date, ttl_days, results FROM RevenueExperiments ORDER BY started_date DESC"
        )
        return [
            {
                "id": r[0], "name": r[1], "status": r[2],
                "started": r[3], "ttl_days": r[4],
                "results": json.loads(r[5] or "{}")
            }
            for r in rows
        ]

    # ── Private ──────────────────────────────────────────────────

    def _request_verdict(self, name: str, hypothesis: str, metric: str,
                          results: dict, age_days: int) -> str:
        account = api_pool.acquire("gemini_calls", preferred_role="research")
        if account is None:
            return "Verdict pending — no Gemini quota available."

        prompt = (
            f"Evaluate this revenue experiment Andrew ran for {age_days} days:\n\n"
            f"Experiment: {name}\n"
            f"Hypothesis: {hypothesis}\n"
            f"Success metric: {metric}\n"
            f"Data collected: {json.dumps(results, indent=2)}\n\n"
            "Did the hypothesis hold? What is the verdict (WINNER/LOSER/ITERATE)? "
            "What specific action should Andrew take next? Be direct and concise."
        )
        try:
            response = self.ai.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"[RevenueLab] Verdict generation failed: {e}")
            return f"Verdict generation failed: {e}"


revenue_lab = RevenueLab()
