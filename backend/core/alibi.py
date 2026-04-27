import logging
from core.black_book import BlackBook
from core.persona import PersonaEngine

logger = logging.getLogger("AlibiProtocol")

class AlibiProtocol:
    """
    Anti-Burnout Reschedule Engine.
    When Deep Work is active, Andrew drafts a polite, TRUTHFUL reschedule
    request and queues it for user approval. Nothing sends automatically.
    """
    def __init__(self):
        self.memory = BlackBook()
        self.ai = PersonaEngine()
        self.in_deep_work = False

    def toggle_deep_work(self, state: bool):
        self.in_deep_work = state
        logger.info(f"Deep Work Mode is now: {'ACTIVE' if state else 'INACTIVE'}")

    def intercept_request(self, sender: str, request_text: str) -> dict:
        """
        If Deep Work is active, drafts a truthful reschedule message
        and returns it for human approval via the outbox.
        Otherwise, passes the request through.
        """
        if not self.in_deep_work:
            return {"status": "passed", "action": "deliver_to_user"}

        logger.info(f"Deep Work active — drafting reschedule reply for {sender}.")

        # Andrew drafts a truthful, polite reschedule — no lies
        prompt = (
            f"Draft a short, polite message to {sender} explaining that the user "
            f"is currently in a focused deep work session and asking to reschedule. "
            f"Their original message: '{request_text[:200]}'. "
            f"Be honest — say the user is busy with focused work. "
            f"Do NOT fabricate excuses, emergencies, or fake reasons. "
            f"Suggest reconnecting in 24-48 hours. Keep it under 3 sentences."
        )

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            draft = response.text.strip()
        except Exception as e:
            logger.error(f"Failed to draft reschedule: {e}")
            draft = f"Hi {sender}, I'm currently in a deep work session and can't respond right now. Can we reconnect tomorrow?"

        self.memory.log_lesson("Reschedule", f"Drafted reschedule reply for {sender} during deep work.")

        return {
            "status": "draft_pending_approval",
            "action": "queue_in_outbox",
            "risk_zone": "yellow",
            "reply_draft": draft
        }

alibi_protocol = AlibiProtocol()
