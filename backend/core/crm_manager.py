import logging
import sqlite3
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CRMManager:
    """
    The Financial Growth Layer.
    Manages Leads, Open Invoices, Bounties, and SaaS Income using SQLite.
    """
    def __init__(self, db_path: str = "data/crm_clients.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS leads (id TEXT PRIMARY KEY, client TEXT, status TEXT, value REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS invoices (id TEXT PRIMARY KEY, client TEXT, status TEXT, amount REAL)''')
        # No seed data — dashboard starts at $0 until Andrew earns real revenue
        conn.commit()
        conn.close()

    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_financial_summary(self) -> Dict[str, Any]:
        """
        Calculates and returns the financial health overview directly from SQLite.
        """
        leads = self._execute_query("SELECT * FROM leads")
        invoices = self._execute_query("SELECT * FROM invoices")

        pending_invoices = sum(inv["amount"] for inv in invoices if inv["status"] == "Pending")
        active_leads = sum(lead["value"] for lead in leads if lead["status"] != "Bounty Claimed")

        # Calculate actual bounty/SaaS income from DB
        bounties_won = sum(lead["value"] for lead in leads if lead["status"] == "Bounty Claimed")
        paid_invoices = sum(inv["amount"] for inv in invoices if inv["status"] == "Paid")

        projected_earnings = pending_invoices + active_leads

        return {
            "bounties_won": bounties_won,
            "paid_income": paid_invoices,
            "pending_invoices": pending_invoices,
            "active_leads_value": active_leads,
            "projected_earnings": projected_earnings,
            "recent_leads": leads,
            "recent_invoices": invoices
        }

    def run_market_research(self) -> str:
        """
        The Researcher Wing. Uses DuckDuckGo Search (Free) to find 'High-CPM' niches.
        """
        try:
            from duckduckgo_search import DDGS
            
            logger.info("Querying DuckDuckGo for High-CPM software engineering niches...")
            results = DDGS().text("high cpm software engineering niches 2026", max_results=1)
            if results:
                return f"DuckDuckGo Research: {results[0].get('body', 'No snippet found.')}"
            raise RuntimeError("DuckDuckGo Search returned no results.")
        except ImportError:
            raise RuntimeError("duckduckgo-search not installed. Run 'pip install duckduckgo-search'.")
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise RuntimeError(f"Market Research failed: {e}")

    def run_niche_arbitrage(self) -> str:
        """
        The Venture Scout (Financial Foresight Engine).
        Finds Micro-SaaS gaps by analyzing forums and Reddit.
        """
        try:
            import requests
            logger.info("Scraping /r/SaaS for niche arbitrage opportunities...")
            headers = {"User-Agent": "Andrew-Agent/1.0 (Oracle Cloud Deployment)"}
            response = requests.get("https://www.reddit.com/r/SaaS/top.json?limit=3&t=week", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                if not posts:
                    return "No trending SaaS niches found this week."
                
                trends = []
                for post in posts:
                    title = post["data"].get("title", "")
                    trends.append(f"- {title}")
                return "Recent Top SaaS Trends:\n" + "\n".join(trends)
            else:
                logger.warning(f"Reddit API returned {response.status_code}")
                return "Reddit API unavailable for niche arbitrage."
        except Exception as e:
            logger.error(f"Niche arbitrage failed: {e}")
            return f"Niche arbitrage error: {e}"

    def get_relocation_savings(self) -> dict:
        """
        Tracks the Financial Runway for the Relocation Blueprint.
        Reads real balance from Coinbase wallet if available.
        """
        logger.info("Calculating Relocation Savings...")
        current_usdt = 0.0
        try:
            from core.coinbase_agent import coinbase_agent
            if coinbase_agent and coinbase_agent.cdp_initialized:
                current_usdt = coinbase_agent.get_usdc_balance()
        except Exception as e:
            logger.warning(f"Cannot read Coinbase balance for relocation savings: {e}")

        return {
            "target_usd": 15000.00,
            "current_usdt": current_usdt,
            "status": "tracking" if current_usdt > 0 else "no_balance_data"
        }

    def generate_monthly_budget(self, parent_allowance: float) -> dict:
        """
        Zero-Based Budgeting. Allocates every single Naira/Dollar from parental
        allowance to ensure survival, while reinvesting into Cloud Computing growth.
        """
        logger.info("Generating Hour-by-Hour and Dollar-by-Dollar Budget...")
        savings = parent_allowance * 0.20
        cloud_certs = parent_allowance * 0.15
        living_expenses = parent_allowance * 0.65
        
        return {
            "allowance_input": parent_allowance,
            "living_expenses": living_expenses,
            "cloud_certification_fund": cloud_certs,
            "emergency_savings": savings,
            "andrew_advice": "I have allocated 15% specifically for your AWS/GCP certs. This is the bridge from allowance to your Cloud Career."
        }

crm_manager = CRMManager()
