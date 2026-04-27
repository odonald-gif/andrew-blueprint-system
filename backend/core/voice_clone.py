import logging
import os
from core.persona import PersonaEngine

logger = logging.getLogger("VoiceClone")

class VoiceClone:
    """
    The True 'Donna' Protocol.
    Intercepts calls and uses ElevenLabs to speak to clients with a hyper-professional voice.
    """
    def __init__(self):
        self.ai = PersonaEngine()
        self.elevenlabs_api_key = os.getenv("ELEVEN_LABS_API_KEY", os.getenv("ELEVENLABS_API_KEY"))
        self.voice_id = os.getenv("ELEVEN_LABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    def intercept_call(self, caller_name: str, urgency: str) -> dict:
        """
        Generates a script and synthesizes voice using ElevenLabs API.
        """
        logger.info(f"Intercepting call from {caller_name} (Urgency: {urgency})")
        
        # 1. Generate the Script
        script = self.ai.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=self.ai.system_prompt + f"\n\nDraft a 2-sentence greeting for a call from {caller_name} with {urgency} urgency. You are answering the phone.",
        ).text.strip()
        
        # 2. Synthesize with ElevenLabs if available
        if not self.elevenlabs_api_key:
            logger.warning("No ElevenLabs API Key. Returning script only for TTS fallback.")
            return {"status": "script_only", "script": script}
            
        try:
            import requests
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            payload = {
                "text": script,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
            }
            resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                # In a real app, we'd save this to a file or stream it to Twilio
                return {"status": "success", "script": script, "audio_bytes_length": len(resp.content)}
            else:
                logger.error(f"ElevenLabs API Error: {resp.text}")
                return {"status": "api_error", "script": script, "error": resp.text}
        except Exception as e:
            return {"status": "error", "script": script, "error": str(e)}
        


voice_clone = VoiceClone()
