import os
import logging
from typing import Dict, Any

try:
    from twilio.rest import Client
except ImportError:
    Client = None

logger = logging.getLogger(__name__)

class VoiceCaller:
    """
    Handles Twilio voice calling capabilities for the "Personal Life" layer.
    Allows Andrew to make outbound calls for errands or emergencies.
    """
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = os.getenv("TWILIO_FROM_PHONE")
        
        self.is_enabled = bool(self.account_sid and self.auth_token and self.from_phone and Client)

        if self.is_enabled:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            logger.warning("Twilio is not configured. Voice caller is disabled.")

    def place_call(self, to_phone: str, twiml_url: str) -> Dict[str, Any]:
        """
        Places an outbound call using Twilio.
        twiml_url is an endpoint on our FastAPI server that returns XML instructions for what Andrew will say.
        """
        if not self.is_enabled:
            return {"status": "Error", "message": "Voice Caller is not configured. Add TWILIO variables to .env."}

        try:
            call = self.client.calls.create(
                to=to_phone,
                from_=self.from_phone,
                url=twiml_url
            )
            logger.info(f"Placed call to {to_phone}. Call SID: {call.sid}")
            return {"status": "Success", "call_sid": call.sid}
        except Exception as e:
            logger.error(f"Failed to place call: {e}")
            return {"status": "Error", "message": str(e)}

voice_caller = VoiceCaller()
