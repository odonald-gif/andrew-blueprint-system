"""
Google Custom Search: Andrew's Eyes on the Internet.

Uses the Google Programmable Search Engine (Custom Search JSON API)
to perform real web searches. This replaces the old Gemini-as-search
workaround and gives Andrew actual web intelligence.

Free tier: 100 queries/day per API key.
With 9 Cloud Console keys, that's up to 900 searches/day.

Requires:
    - GOOGLE_CSE_ID in .env (the Programmable Search Engine ID)
    - At least one GOOGLE_CLOUD_KEY_* in .env (the API key with Custom Search enabled)
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional

from core.api_pool import api_pool

logger = logging.getLogger(__name__)

# Google Custom Search API endpoint
CSE_API_URL = "https://www.googleapis.com/customsearch/v1"

# Search Engine ID — configured in .env
SEARCH_ENGINE_ID = os.getenv("GOOGLE_CSE_ID", "")


class GoogleSearch:
    """
    Andrew's real web search capability.

    Uses the Google Programmable Search Engine (Custom Search JSON API)
    to query the open web. Results are structured and ready for
    downstream analysis by Gemini or direct use in modules like
    MarketScanner, ScoutEngine, BountyHunter, etc.
    """

    def __init__(self):
        self.cse_id = SEARCH_ENGINE_ID
        if not self.cse_id:
            logger.warning(
                "[GoogleSearch] GOOGLE_CSE_ID not set in .env. "
                "Web search will be unavailable."
            )

    def search(
        self,
        query: str,
        num_results: int = 5,
        search_type: Optional[str] = None,
        date_restrict: Optional[str] = None,
        site_search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a web search via Google Custom Search API.

        Args:
            query:         The search query string.
            num_results:   Number of results to return (1-10, API max per call).
            search_type:   Optional. Set to 'image' for image search.
            date_restrict: Optional. Restrict results by age, e.g. 'd7' (last 7 days),
                           'w1' (last week), 'm1' (last month).
            site_search:   Optional. Restrict results to a specific site, e.g. 'reddit.com'.

        Returns:
            Dict with 'status', 'query', 'results' (list of dicts with title, link, snippet).
        """
        if not self.cse_id:
            return {
                "status": "error",
                "reason": "GOOGLE_CSE_ID not configured in .env",
                "results": [],
            }

        # Acquire a Cloud Console key via the API pool (search requires Console tier)
        account_idx = api_pool.acquire("search_queries", preferred_role="scout")
        if account_idx is None:
            logger.warning("[GoogleSearch] No search quota available across all accounts.")
            return {
                "status": "no_quota",
                "reason": "All 9 accounts exhausted their search quota for today.",
                "results": [],
            }

        api_key = api_pool.get_key(account_idx, tier="console")
        if not api_key:
            # Fallback: try the studio key (some users may have CSE enabled on studio keys)
            api_key = api_pool.get_key(account_idx, tier="studio")
        if not api_key:
            return {
                "status": "error",
                "reason": f"No API key found for account {account_idx}.",
                "results": [],
            }

        # Build request parameters
        params = {
            "key": api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(num_results, 10),
        }

        if search_type:
            params["searchType"] = search_type
        if date_restrict:
            params["dateRestrict"] = date_restrict
        if site_search:
            params["siteSearch"] = site_search

        try:
            response = requests.get(CSE_API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])

                results = []
                for item in items:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("displayLink", ""),
                    })

                logger.info(
                    f"[GoogleSearch] '{query}' → {len(results)} results "
                    f"(account {account_idx})"
                )

                return {
                    "status": "success",
                    "query": query,
                    "total_results": data.get("searchInformation", {}).get(
                        "totalResults", "0"
                    ),
                    "results": results,
                    "account_used": account_idx,
                }

            elif response.status_code == 429:
                logger.warning(
                    f"[GoogleSearch] Rate limited on account {account_idx}. "
                    "Quota may be exhausted."
                )
                return {
                    "status": "rate_limited",
                    "reason": "API quota exhausted for this key.",
                    "results": [],
                }

            else:
                error_detail = response.json().get("error", {}).get("message", response.text[:200])
                logger.error(
                    f"[GoogleSearch] API error {response.status_code}: {error_detail}"
                )
                return {
                    "status": "error",
                    "reason": f"HTTP {response.status_code}: {error_detail}",
                    "results": [],
                }

        except requests.exceptions.Timeout:
            logger.error("[GoogleSearch] Request timed out.")
            return {"status": "error", "reason": "Request timed out.", "results": []}
        except Exception as e:
            logger.error(f"[GoogleSearch] Unexpected error: {e}")
            return {"status": "error", "reason": str(e), "results": []}

    def multi_search(
        self,
        queries: List[str],
        num_results: int = 3,
        date_restrict: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute multiple search queries and aggregate results.
        Used by MarketScanner for daily intelligence sweeps.

        Args:
            queries:       List of search query strings.
            num_results:   Results per query (1-10).
            date_restrict: Optional time restriction for all queries.

        Returns:
            Dict with 'status', 'total_queries', 'successful', 'failed',
            and 'results' (dict mapping query → result list).
        """
        all_results = {}
        successful = 0
        failed = 0

        for query in queries:
            result = self.search(
                query=query,
                num_results=num_results,
                date_restrict=date_restrict,
            )

            if result["status"] == "success":
                all_results[query] = result["results"]
                successful += 1
            elif result["status"] == "no_quota":
                # Stop early if we're out of quota
                logger.warning(
                    f"[GoogleSearch] Quota exhausted after {successful} queries. "
                    f"Stopping multi_search early."
                )
                break
            else:
                all_results[query] = []
                failed += 1

        return {
            "status": "complete" if successful > 0 else "no_quota",
            "total_queries": len(queries),
            "successful": successful,
            "failed": failed,
            "results": all_results,
        }

    def search_site(
        self,
        query: str,
        site: str,
        num_results: int = 5,
        date_restrict: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method: search within a specific site.
        E.g., search_site("AI automation jobs", "upwork.com")
        """
        return self.search(
            query=query,
            num_results=num_results,
            site_search=site,
            date_restrict=date_restrict,
        )

    def search_recent(
        self,
        query: str,
        days: int = 7,
        num_results: int = 5,
    ) -> Dict[str, Any]:
        """
        Convenience method: search for recent results only.
        """
        return self.search(
            query=query,
            num_results=num_results,
            date_restrict=f"d{days}",
        )


# Singleton — Andrew's search eyes
google_search = GoogleSearch()
