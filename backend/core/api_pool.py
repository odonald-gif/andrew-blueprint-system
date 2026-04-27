"""
API Pool: Andrew's Nine-Account Resource Governor.

Each of the 9 Google accounts has TWO key tiers:
  - AI Studio key  (free, ~1500 Gemini calls/day)
  - Cloud Console key (higher limits, access to Search/Gmail/Calendar APIs)

Andrew defaults to AI Studio (free). Escalates to Cloud Console when:
  1. AI Studio quota is exhausted for that account
  2. The task requires non-Gemini APIs (search, gmail, calendar)
  3. A caller explicitly requests the premium tier
"""

import os
import logging
from datetime import date
from typing import Optional, Dict
from core.black_book import BlackBook

logger = logging.getLogger(__name__)

# Role assignments for each account slot (0-indexed)
ACCOUNT_ROLES = {
    0: "brain",       # Andrew's core reasoning
    1: "scout",       # Market intelligence & search
    2: "memory",      # Sheets/Drive data layer
    3: "outreach",    # Gmail / communication
    4: "worker",      # Cloud Functions / execution
    5: "monitor",     # Web presence, YouTube
    6: "finance",     # Financial tracking
    7: "backup",      # Failover brain
    8: "research",    # Experimental / R&D
}

# Daily quota ceilings per account per tier
DAILY_QUOTA = {
    "gemini_calls":   {"studio": 1400, "console": 1400},
    "search_queries": {"studio": 0,    "console": 90},    # Search API only on Console
    "gmail_sends":    {"studio": 0,    "console": 450},   # Gmail API only on Console
    "calendar_reads": {"studio": 0,    "console": 900},   # Calendar API only on Console
}

# API types that REQUIRE Cloud Console keys (not available on AI Studio)
CONSOLE_ONLY_APIS = {"search_queries", "gmail_sends", "calendar_reads"}


class ApiPool:
    """
    Manages dual-tier keys across 9 Google accounts.

    Key loading from environment:
      GEMINI_API_KEY_0  ... _8   → AI Studio keys (free tier)
      GOOGLE_CLOUD_KEY_0 ... _8  → Cloud Console keys (premium tier)
      GEMINI_API_KEY             → Fallback if individual keys aren't set
    """

    def __init__(self):
        self.memory = BlackBook()
        self._ensure_table()
        self._studio_keys: Dict[int, str] = {}
        self._console_keys: Dict[int, str] = {}
        self._load_keys()

    def _load_keys(self):
        """Load both tiers of API keys for all 9 accounts."""
        fallback_key = os.getenv("GEMINI_API_KEY", "")
        studio_loaded = 0
        console_loaded = 0

        for idx in range(9):
            # AI Studio keys (free tier)
            studio_key = os.getenv(f"GEMINI_API_KEY_{idx}", "")
            if studio_key:
                self._studio_keys[idx] = studio_key
                studio_loaded += 1
            elif fallback_key:
                self._studio_keys[idx] = fallback_key

            # Cloud Console keys (premium tier)
            console_key = os.getenv(f"GOOGLE_CLOUD_KEY_{idx}", "")
            if console_key:
                self._console_keys[idx] = console_key
                console_loaded += 1

        logger.info(
            f"[ApiPool] Loaded {studio_loaded}/9 AI Studio keys, "
            f"{console_loaded}/9 Cloud Console keys. "
            f"Fallback: {'yes' if fallback_key else 'no'}"
        )

        if studio_loaded == 0 and not fallback_key:
            logger.error("[ApiPool] NO API KEYS CONFIGURED. Andrew cannot think.")

    def _ensure_table(self):
        self.memory.execute_query("""
            CREATE TABLE IF NOT EXISTS ApiQuota (
                account_idx  INTEGER NOT NULL,
                tier         TEXT    NOT NULL DEFAULT 'studio',
                quota_date   TEXT    NOT NULL,
                api_type     TEXT    NOT NULL,
                used         INTEGER DEFAULT 0,
                PRIMARY KEY (account_idx, tier, quota_date, api_type)
            )
        """)

    # ── Public Interface ─────────────────────────────────────────

    def get_key(self, account_idx: int, tier: str = "studio") -> Optional[str]:
        """Return the API key for a specific account and tier."""
        if tier == "console":
            return self._console_keys.get(account_idx)
        return self._studio_keys.get(account_idx)

    def acquire(
        self,
        api_type: str,
        preferred_role: Optional[str] = None,
        tier: Optional[str] = None
    ) -> Optional[int]:
        """
        Return an account index with remaining quota for api_type.

        Tier selection logic:
          - If api_type is console-only (search, gmail, calendar) → forces console tier
          - If tier='console' is explicitly requested → uses console
          - Otherwise → tries AI Studio first, falls back to Console if exhausted

        Returns None if all accounts are exhausted.
        """
        today = str(date.today())

        # Determine which tiers to try and in what order
        if api_type in CONSOLE_ONLY_APIS:
            tiers_to_try = ["console"]
        elif tier == "console":
            tiers_to_try = ["console"]
        elif tier == "studio":
            tiers_to_try = ["studio"]
        else:
            # Default: free first, premium failover
            tiers_to_try = ["studio", "console"]

        # Build ordered candidate list: preferred role first, then others
        candidates = list(range(9))
        if preferred_role:
            preferred = [i for i, r in ACCOUNT_ROLES.items() if r == preferred_role]
            others = [i for i in candidates if i not in preferred]
            candidates = preferred + others

        for try_tier in tiers_to_try:
            key_pool = self._studio_keys if try_tier == "studio" else self._console_keys
            ceiling = DAILY_QUOTA.get(api_type, {}).get(try_tier, 1000)

            # Skip tier if ceiling is 0 (API not available on this tier)
            if ceiling == 0:
                continue

            for idx in candidates:
                if idx not in key_pool:
                    continue

                used = self._get_used(idx, try_tier, today, api_type)
                if used < ceiling:
                    self._increment(idx, try_tier, today, api_type)
                    logger.info(
                        f"[ApiPool] Account {idx} ({ACCOUNT_ROLES[idx]}) "
                        f"[{try_tier.upper()}] acquired for {api_type} ({used+1}/{ceiling})"
                    )
                    return idx

        logger.warning(f"[ApiPool] All accounts exhausted for {api_type} across all tiers.")
        return None

    def get_status(self) -> dict:
        """Return today's usage across all accounts, both tiers."""
        today = str(date.today())
        rows = self.memory.execute_query(
            "SELECT account_idx, tier, api_type, used FROM ApiQuota WHERE quota_date = ?",
            (today,)
        )
        status = {}
        for i in range(9):
            status[i] = {
                "role": ACCOUNT_ROLES[i],
                "studio_key": i in self._studio_keys,
                "console_key": i in self._console_keys,
                "usage": {"studio": {}, "console": {}}
            }
        for account_idx, tier, api_type, used in rows:
            ceiling = DAILY_QUOTA.get(api_type, {}).get(tier, 1000)
            status[account_idx]["usage"][tier][api_type] = f"{used}/{ceiling}"
        return status

    def total_remaining(self, api_type: str) -> int:
        """Sum of remaining quota across all 9 accounts, both tiers."""
        today = str(date.today())
        total_capacity = 0
        for tier in ["studio", "console"]:
            ceiling = DAILY_QUOTA.get(api_type, {}).get(tier, 0)
            key_pool = self._studio_keys if tier == "studio" else self._console_keys
            total_capacity += ceiling * len(key_pool)

        rows = self.memory.execute_query(
            "SELECT SUM(used) FROM ApiQuota WHERE quota_date = ? AND api_type = ?",
            (today, api_type)
        )
        total_used = rows[0][0] or 0
        return max(0, total_capacity - total_used)

    # ── Private Helpers ──────────────────────────────────────────

    def _get_used(self, account_idx: int, tier: str, today: str, api_type: str) -> int:
        rows = self.memory.execute_query(
            "SELECT used FROM ApiQuota WHERE account_idx=? AND tier=? AND quota_date=? AND api_type=?",
            (account_idx, tier, today, api_type)
        )
        return rows[0][0] if rows else 0

    def _increment(self, account_idx: int, tier: str, today: str, api_type: str):
        self.memory.execute_query("""
            INSERT INTO ApiQuota (account_idx, tier, quota_date, api_type, used)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(account_idx, tier, quota_date, api_type)
            DO UPDATE SET used = used + 1
        """, (account_idx, tier, today, api_type))


api_pool = ApiPool()
