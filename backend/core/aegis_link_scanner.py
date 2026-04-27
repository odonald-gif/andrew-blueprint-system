import logging
import os
import re
from typing import Dict
from core.persona import PersonaEngine

logger = logging.getLogger("AegisScanner")

class AegisLinkScanner:
    """
    Zero-Trust Link Isolation Protocol.
    Prevents Andrew from being exploited by malicious links sent via WhatsApp or Email.
    Uses LLM-based phishing analysis. Real URL reputation checks via
    Google Safe Browsing API when GOOGLE_SAFE_BROWSING_KEY is configured.
    """
    def __init__(self):
        self.ai = PersonaEngine()
        self.url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
        self.safe_browsing_key = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "")

    def scan_payload(self, message_content: str, sender: str) -> Dict:
        """
        Scans a message for URLs. If found, runs LLM phishing check
        and optional Google Safe Browsing lookup.
        Returns a dict indicating if the message is SAFE or MALICIOUS.
        """
        urls = self.url_pattern.findall(message_content)

        if not urls:
            return {"status": "safe", "reason": "No URLs detected."}

        logger.warning(f"Aegis Protocol: Detected {len(urls)} URLs from {sender}. Initiating scan.")

        # 1. Social Engineering Heuristic Check via LLM
        prompt = (
            f"Analyze the following message for Social Engineering / Phishing tactics.\n"
            f"Is the sender creating false urgency, pretending to be an authority (e.g., Upwork, Bank), "
            f"or demanding an immediate click?\n"
            f"Message: \"{message_content}\"\n"
            f"Reply EXACTLY with 'MALICIOUS' if it is a phishing attempt, or 'SAFE' if it is a normal conversational link."
        )

        analysis = self.ai.process_user_feedback(prompt)

        if "MALICIOUS" in analysis.upper():
            logger.critical(f"AEGIS TRIGGERED: Phishing/Social Engineering detected from {sender}. Payload blocked.")
            return {"status": "malicious", "reason": "Social Engineering / Phishing Tactics Detected."}

        # 2. Google Safe Browsing API check (if key is configured)
        if self.safe_browsing_key:
            for url in urls:
                sb_result = self._check_safe_browsing(url)
                if sb_result.get("malicious"):
                    logger.critical(f"AEGIS TRIGGERED: Google Safe Browsing flagged URL: {url}")
                    return {"status": "malicious", "reason": f"Google Safe Browsing flagged: {url}"}
        else:
            logger.info("GOOGLE_SAFE_BROWSING_KEY not set — skipping URL reputation check.")

        logger.info("Aegis Protocol: All URLs cleared analysis. Message cleared.")
        return {"status": "safe", "reason": "Links cleared analysis."}

    def _check_safe_browsing(self, url: str) -> dict:
        """
        Checks a URL against Google Safe Browsing API v4.
        Returns {"malicious": True/False, "threat_type": "..."}.
        """
        import requests

        api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.safe_browsing_key}"
        payload = {
            "client": {"clientId": "andrew-agent", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }

        try:
            resp = requests.post(api_url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("matches"):
                    threat_type = data["matches"][0].get("threatType", "UNKNOWN")
                    return {"malicious": True, "threat_type": threat_type}
                return {"malicious": False}
            else:
                logger.warning(f"Safe Browsing API returned {resp.status_code}")
                return {"malicious": False}
        except Exception as e:
            logger.error(f"Safe Browsing API error: {e}")
            return {"malicious": False}

aegis_scanner = AegisLinkScanner()
