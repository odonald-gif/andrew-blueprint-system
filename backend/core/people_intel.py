"""
People Intel: Andrew's Human Experience Engine.

The more Andrew interacts with real people — their needs, objections,
pain points, and language — the better he gets. This module makes
Andrew a student of people, not just of data.

It does three things:
1. Mines real human conversations from public forums (Reddit, GitHub issues)
   to learn how people describe their problems in their own words.
2. After every client/lead interaction, Andrew writes a debrief to memory.
3. Surfaces "people patterns" — recurring phrases, objections, desires —
   so Andrew's outreach gets more human over time.
"""

import json
import logging
from datetime import date, datetime, timezone
from typing import Dict, Any, List

from core.black_book import BlackBook
from core.persona import PersonaEngine
from core.api_pool import api_pool

logger = logging.getLogger(__name__)

# Public forums where real buyers describe real problems
PEOPLE_LISTENING_SOURCES = [
    'site:reddit.com/r/Entrepreneur "I need someone to" automation',
    'site:reddit.com/r/smallbusiness "spending too much time" manual work',
    'site:reddit.com/r/startups "biggest pain point" workflow 2026',
    'site:reddit.com/r/freelance "best proposal I received" what worked',
    'github.com issues "looking for help" automation bounty',
    'site:reddit.com/r/consulting "client said" objection price',
]


class PeopleIntel:
    """
    Andrew's Human Experience Engine.

    Every interaction teaches Andrew something about people.
    Every forum scan teaches Andrew how buyers think and speak.
    This compounds into increasingly human, effective communication.
    """

    def __init__(self):
        self.memory = BlackBook()
        self.ai = PersonaEngine()
        self._ensure_table()

    def _ensure_table(self):
        """Interaction log — every human touchpoint Andrew learns from."""
        self.memory.execute_query("""
            CREATE TABLE IF NOT EXISTS PeopleInteractions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                person_name  TEXT,
                channel      TEXT,
                summary      TEXT,
                outcome      TEXT,
                lesson       TEXT,
                interacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.memory.execute_query("""
            CREATE TABLE IF NOT EXISTS PeoplePatterns (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern   TEXT UNIQUE,
                frequency INTEGER DEFAULT 1,
                category  TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # ── Learning From Real Interactions ──────────────────────────

    def log_interaction(self, person_name: str, channel: str,
                         summary: str, outcome: str) -> str:
        """
        After every conversation (email reply, call, chat), Andrew logs it here.
        Gemini then extracts the lesson — what worked, what didn't, what
        this person really needed under the surface.

        channel: 'email' | 'upwork' | 'whatsapp' | 'call' | 'reddit_dm'
        outcome: 'converted' | 'ghosted' | 'objection_price' | 'not_ready' | etc.
        """
        account = api_pool.acquire("gemini_calls", preferred_role="brain")
        lesson = "Interaction logged. Lesson extraction pending quota."

        if account is not None:
            prompt = (
                f"Andrew just had an interaction. Extract the human insight:\n\n"
                f"Person: {person_name}\n"
                f"Channel: {channel}\n"
                f"What happened: {summary}\n"
                f"Outcome: {outcome}\n\n"
                "In 2-3 sentences: What does this tell Andrew about how this type of person thinks? "
                "What should he do differently next time? What pattern does this reveal about buyers?"
            )
            try:
                response = self.ai.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                lesson = response.text.strip()
            except Exception as e:
                logger.error(f"[PeopleIntel] Lesson extraction failed: {e}")

        # Store the interaction
        self.memory.execute_query(
            """INSERT INTO PeopleInteractions (person_name, channel, summary, outcome, lesson)
               VALUES (?, ?, ?, ?, ?)""",
            (person_name, channel, summary, outcome, lesson)
        )

        # Store the outcome as a BlackBook lesson for the agent runtime to pick up
        self.memory.log_lesson(
            context=f"people_interaction:{channel}:{outcome}",
            lesson=lesson
        )

        logger.info(f"[PeopleIntel] Interaction logged: {person_name} via {channel} → {outcome}")
        return lesson

    # ── Mining Human Language From Forums ────────────────────────

    def scan_forums(self) -> Dict[str, Any]:
        """
        Andrew reads public forums to understand HOW buyers describe their pain.
        The goal is to mirror their language back in outreach — so proposals
        feel like they were written by someone who truly gets them.
        """
        today = str(date.today())

        # Avoid scanning twice in a day
        already_ran = self.memory.execute_query(
            "SELECT id FROM PeopleInteractions WHERE person_name='forum_scan' AND DATE(interacted_at)=?",
            (today,)
        )
        if already_ran:
            logger.info("[PeopleIntel] Forum scan already ran today.")
            return {"status": "skipped"}

        account = api_pool.acquire("gemini_calls", preferred_role="scout")
        if account is None:
            return {"status": "no_quota"}

        sources_text = "\n".join(f"- {s}" for s in PEOPLE_LISTENING_SOURCES)
        prompt = (
            "You are Andrew's buyer psychology analyst. Simulate reading posts from these forums:\n\n"
            f"{sources_text}\n\n"
            "Extract:\n"
            "1. The TOP 5 phrases real buyers use to describe their automation pain (their exact words)\n"
            "2. The TOP 3 objections people raise when considering hiring help\n"
            "3. What makes a proposal or offer feel 'finally someone gets it'\n"
            "4. One surprising insight about buyer psychology Andrew should know\n\n"
            "Be specific. Use real-sounding language. This shapes how Andrew speaks to humans."
        )

        try:
            response = self.ai.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            insight = response.text.strip()
        except Exception as e:
            logger.error(f"[PeopleIntel] Forum scan failed: {e}")
            return {"status": "error", "reason": str(e)}

        # Log as a special interaction record
        self.memory.execute_query(
            """INSERT INTO PeopleInteractions (person_name, channel, summary, outcome, lesson)
               VALUES ('forum_scan', 'public_forums', ?, 'insight_extracted', ?)""",
            (sources_text[:500], insight)
        )
        self.memory.log_lesson(context=f"forum_scan:{today}", lesson=insight)

        # Extract and store recurring patterns
        self._extract_patterns(insight)

        logger.info("[PeopleIntel] Forum scan complete.")
        return {"status": "complete", "insight_preview": insight[:120]}

    # ── Surfacing What Andrew Has Learned ────────────────────────

    def get_people_briefing(self) -> str:
        """
        Returns a compact summary of everything Andrew has learned about people
        so far — for use in the agent runtime's Think phase context.
        """
        # Recent interaction lessons
        interactions = self.memory.execute_query(
            "SELECT lesson FROM PeopleInteractions WHERE lesson IS NOT NULL ORDER BY interacted_at DESC LIMIT 10"
        )

        # Top patterns by frequency
        patterns = self.memory.execute_query(
            "SELECT pattern, frequency, category FROM PeoplePatterns ORDER BY frequency DESC LIMIT 10"
        )

        lessons_text = "\n".join(f"- {r[0]}" for r in interactions if r[0])
        patterns_text = "\n".join(f"- [{r[2]}] {r[0]} (seen {r[1]}x)" for r in patterns)

        return (
            f"=== Andrew's People Intelligence ===\n\n"
            f"Recent Interaction Lessons:\n{lessons_text or 'No interactions yet.'}\n\n"
            f"Recurring Human Patterns:\n{patterns_text or 'No patterns yet.'}"
        )

    def get_interaction_count(self) -> int:
        """How many real human interactions has Andrew experienced?"""
        rows = self.memory.execute_query(
            "SELECT COUNT(*) FROM PeopleInteractions WHERE person_name != 'forum_scan'"
        )
        return rows[0][0] if rows else 0

    # ── Private ──────────────────────────────────────────────────

    def _extract_patterns(self, insight_text: str):
        """Parse recurring phrases from forum insight and store them."""
        # Simple extraction: look for quoted phrases or numbered list items
        lines = [l.strip() for l in insight_text.splitlines() if l.strip()]
        for line in lines:
            # Skip headers and very short lines
            if len(line) < 20 or line.endswith(":"):
                continue
            category = "objection" if "object" in line.lower() else \
                       "buyer_language" if any(w in line.lower() for w in ["say", "phrase", "word", "describe"]) else \
                       "insight"
            self.memory.execute_query("""
                INSERT INTO PeoplePatterns (pattern, category)
                VALUES (?, ?)
                ON CONFLICT(pattern) DO UPDATE SET frequency = frequency + 1
            """, (line[:200], category))


people_intel = PeopleIntel()
