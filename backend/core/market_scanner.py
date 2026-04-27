"""
Market Scanner: Andrew's Daily Intelligence Sweep.

Uses Google Custom Search (Programmable Search Engine) to scan markets
every morning. Looks for: what people are paying for, unmet needs,
trending skills, and new earning opportunities. Synthesizes findings
via Gemini and writes them to BlackBook as Lessons.

Andrew doesn't guess what the market wants — he reads it daily.
"""

import logging
from datetime import date
from typing import List, Dict, Any

from core.black_book import BlackBook
from core.persona import PersonaEngine
from core.api_pool import api_pool
from core.google_search import google_search

logger = logging.getLogger(__name__)

# Searches Andrew runs every day — tuned for revenue intelligence
DAILY_SEARCH_QUERIES = [
    # What are people actively paying for RIGHT NOW?
    "upwork AI automation jobs posted today $50+/hr",
    "upwork 'AI agent' OR 'n8n' OR 'make.com' new job 2026",
    # What problems have no good solution?
    'reddit "I wish there was a tool" AI automation 2026',
    'reddit "does anyone automate" business workflow 2026',
    # What skills command premium prices?
    "freelance AI consulting rates 2026 highest paying",
    # What is selling on micro-SaaS marketplaces?
    "microacquire profitable AI tool revenue 2026",
    # What content is exploding in engagement?
    "youtube trending AI productivity tools 2026",
    # Who is hiring and paying well?
    "linkedin 'hiring' AI automation specialist remote 2026",
]


class MarketScanner:
    """
    Runs Andrew's daily market intelligence sweep.
    Uses Google Custom Search for real web data, then Gemini to synthesize.
    Stores actionable insights as Lessons in the BlackBook.
    """

    def __init__(self):
        self.memory = BlackBook()
        self.ai = PersonaEngine()

    def run(self) -> Dict[str, Any]:
        """
        Execute the full daily scan. Should be called once per day,
        ideally in the morning before Andrew plans his outreach.
        Returns a summary of what was found.
        """
        today = str(date.today())

        # Avoid double-scanning the same day
        already_ran = self.memory.execute_query(
            "SELECT lesson FROM Lessons WHERE context = ? ORDER BY timestamp DESC LIMIT 1",
            (f"market_scan:{today}",)
        )
        if already_ran:
            logger.info("[MarketScanner] Already scanned today. Skipping.")
            return {"status": "skipped", "reason": "Already ran today"}

        logger.info("[MarketScanner] Starting daily intelligence sweep via Google Search...")

        # Phase 1: Real web search via Google Custom Search API
        search_results = google_search.multi_search(
            queries=DAILY_SEARCH_QUERIES,
            num_results=3,
            date_restrict="m1",  # Last month for freshness
        )

        if search_results["status"] == "no_quota":
            logger.warning("[MarketScanner] No search quota available. Falling back to Gemini-only.")
            # Fallback: use Gemini's knowledge as a backup
            return self._fallback_gemini_scan(today)

        # Phase 2: Feed search results to Gemini for synthesis
        raw_data_summary = self._format_search_results(search_results["results"])

        gemini_account = api_pool.acquire("gemini_calls", preferred_role="scout")
        if gemini_account is None:
            # Store raw results even without Gemini synthesis
            self.memory.log_lesson(
                context=f"market_scan:{today}",
                lesson=f"[Raw Search Data - Gemini unavailable]\n{raw_data_summary}"
            )
            return {"status": "partial", "reason": "Search complete but Gemini unavailable for synthesis"}

        try:
            synthesis_prompt = (
                "You are Andrew's Market Intelligence analyst. "
                "Below are REAL search results from today's web scan.\n\n"
                f"{raw_data_summary}\n\n"
                "Synthesize these into a concise daily briefing. For each topic, answer:\n"
                "- What is currently in demand?\n"
                "- What are people paying?\n"
                "- What gaps exist with no good solution?\n\n"
                "End with ONE 'Top Opportunity of the Day' — the single highest-leverage action "
                "Andrew could take today to move toward $10k+ in revenue. Be specific and actionable."
            )

            response = self.ai.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=synthesis_prompt,
            )
            raw_insight = response.text.strip()
        except Exception as e:
            logger.error(f"[MarketScanner] Gemini synthesis failed: {e}")
            raw_insight = f"[Synthesis failed — raw data below]\n{raw_data_summary}"

        # Store as a lesson Andrew can recall in future cycles
        self.memory.log_lesson(
            context=f"market_scan:{today}",
            lesson=raw_insight
        )

        # Extract the top opportunity for today's action
        top_opportunity = self._extract_top_opportunity(raw_insight)
        if top_opportunity:
            self.memory.set_preference("todays_top_opportunity", top_opportunity)
            logger.info(f"[MarketScanner] Top opportunity: {top_opportunity[:80]}...")

        logger.info(
            f"[MarketScanner] Daily scan complete. "
            f"Searched {search_results['successful']}/{search_results['total_queries']} queries."
        )
        return {
            "status": "complete",
            "insights_stored": True,
            "top_opportunity": top_opportunity,
            "queries_searched": search_results["successful"],
            "queries_failed": search_results["failed"],
        }

    def get_recent_insights(self, days: int = 7) -> List[str]:
        """Pull the last N days of market scan lessons for Andrew's context."""
        rows = self.memory.execute_query(
            "SELECT lesson FROM Lessons WHERE context LIKE 'market_scan:%' ORDER BY timestamp DESC LIMIT ?",
            (days,)
        )
        return [r[0] for r in rows]

    # ── Private ──────────────────────────────────────────────────

    def _format_search_results(self, results: Dict[str, list]) -> str:
        """Format multi_search results into a readable prompt for Gemini."""
        sections = []
        for query, items in results.items():
            section = f"### Search: \"{query}\"\n"
            if items:
                for i, item in enumerate(items, 1):
                    section += (
                        f"  {i}. **{item['title']}** ({item['source']})\n"
                        f"     {item['snippet']}\n"
                        f"     Link: {item['link']}\n"
                    )
            else:
                section += "  No results found.\n"
            sections.append(section)
        return "\n".join(sections)

    def _fallback_gemini_scan(self, today: str) -> Dict[str, Any]:
        """Fallback: use Gemini's own knowledge when search quota is exhausted."""
        gemini_account = api_pool.acquire("gemini_calls", preferred_role="scout")
        if gemini_account is None:
            return {"status": "no_quota", "reason": "Both search and Gemini quotas exhausted"}

        try:
            queries_text = "\n".join(f"- {q}" for q in DAILY_SEARCH_QUERIES)
            fallback_prompt = (
                "You are Andrew's Market Intelligence analyst. "
                "Research the following topics and return a concise daily briefing:\n\n"
                f"{queries_text}\n\n"
                "For each topic, answer: What is currently in demand? What are people paying? "
                "What gaps exist with no good solution? "
                "End with ONE 'Top Opportunity of the Day' — the single highest-leverage action "
                "Andrew could take today to move toward $10k+ in revenue. Be specific and actionable."
            )

            response = self.ai.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=fallback_prompt,
            )
            raw_insight = response.text.strip()

            self.memory.log_lesson(
                context=f"market_scan:{today}",
                lesson=f"[Gemini fallback — no web search]\n{raw_insight}"
            )

            top_opportunity = self._extract_top_opportunity(raw_insight)
            if top_opportunity:
                self.memory.set_preference("todays_top_opportunity", top_opportunity)

            return {
                "status": "complete_fallback",
                "insights_stored": True,
                "top_opportunity": top_opportunity,
            }
        except Exception as e:
            logger.error(f"[MarketScanner] Fallback Gemini scan also failed: {e}")
            return {"status": "error", "reason": str(e)}

    def _extract_top_opportunity(self, insight_text: str) -> str:
        """Parse the Top Opportunity line from Gemini's response."""
        for line in insight_text.splitlines():
            if "top opportunity" in line.lower() or "highest-leverage" in line.lower():
                return line.strip()
        # Fallback: return last non-empty line
        lines = [l.strip() for l in insight_text.splitlines() if l.strip()]
        return lines[-1] if lines else ""


market_scanner = MarketScanner()

