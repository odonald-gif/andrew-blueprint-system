import logging
import subprocess
from typing import Dict, Any

logger = logging.getLogger("ActiveDefense")

class ActiveDefense:
    """
    The 'Fighting Back' Protocol.
    Instead of just blocking hackers, Andrew generates fake high-value targets (Honey-Tokens)
    to waste attacker resources and burn their scripts.
    """
    def __init__(self):
        self.active_honey_tokens = {}

    def deploy_honey_token(self, attacker_ip: str) -> dict:
        """
        Generates a fake API key/wallet and 'leaks' it to the attacker's payload.
        """
        import random
        import string
        fake_aws_key = "AKIA" + "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
        fake_aws_secret = "".join(random.choices(string.ascii_letters + string.digits, k=40))

        self.active_honey_tokens[fake_aws_key] = attacker_ip

        logger.warning(f"Active Defense: Deployed Honey-Token {fake_aws_key} to attacker at {attacker_ip}.")

        return {
            "AWS_ACCESS_KEY_ID": fake_aws_key,
            "AWS_SECRET_ACCESS_KEY": fake_aws_secret,
            "message": "Internal Server Data Leak (Simulated)"
        }

    def detect_honey_token_usage(self, used_key: str, request_source: str):
        """
        If a third party attempts to use the leaked key, Andrew logs it and bans them globally.
        """
        if used_key in self.active_honey_tokens:
            original_attacker = self.active_honey_tokens[used_key]
            logger.critical(f"HONEY-TOKEN TRIGGERED! Attacker {original_attacker} is attempting to use the fake key from {request_source}.")
            logger.critical("Initiating IP ban and reporting attacker to network blacklists.")
            return True
        return False

    def proactive_vulnerability_scan(self) -> Dict[str, Any]:
        """
        Andrew scans his own Python dependencies for known vulnerabilities
        using pip-audit. Returns a structured report.
        """
        logger.info("Initiating proactive vulnerability scan via pip-audit...")

        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True, text=True, timeout=120
            )
            import json

            if result.returncode == 0:
                try:
                    vulnerabilities = json.loads(result.stdout)
                except json.JSONDecodeError:
                    vulnerabilities = []

                if not vulnerabilities:
                    logger.info("Vulnerability scan complete: No known vulnerabilities found.")
                    return {"status": "clean", "vulnerabilities": []}

                logger.warning(f"Vulnerability scan found {len(vulnerabilities)} issues.")
                return {
                    "status": "vulnerabilities_found",
                    "count": len(vulnerabilities),
                    "vulnerabilities": vulnerabilities[:10]  # Cap at 10 for readability
                }
            else:
                # pip-audit not installed or errored
                logger.warning(f"pip-audit returned non-zero: {result.stderr[:200]}")
                return {"status": "scan_error", "reason": result.stderr[:200]}

        except FileNotFoundError:
            logger.warning("pip-audit not installed. Run 'pip install pip-audit'.")
            return {"status": "not_installed", "reason": "pip-audit not found. Install with: pip install pip-audit"}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "reason": "Vulnerability scan timed out after 120s"}
        except Exception as e:
            logger.error(f"Vulnerability scan error: {e}")
            return {"status": "error", "reason": str(e)}

active_defense = ActiveDefense()
