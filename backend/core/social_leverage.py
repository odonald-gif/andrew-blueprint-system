import os
import logging
from dotenv import load_dotenv
from google import genai
import json

load_dotenv()
logger = logging.getLogger(__name__)

class NLPParser:
    """
    Scans raw text (emails, meeting notes, IMs) using GenAI to figure out if someone owes the User a favor.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def scan_for_leverage(self, text_content: str, user_name: str = "User") -> dict:
        """
        Uses GenAI to determine if 'text_content' implies a favor was given.
        Returns a dict: {'owed_by': 'Name', 'owed_to': 'Name', 'description': 'What they owe for', 'is_valid': True/False}
        """
        if not self.client:
            logger.error("No Gemini API key found for NLP.")
            return {"is_valid": False}
            
        prompt = f"""
        Act as Andrew, an elite executive assistant. Read the following text and determine if {user_name} just did a significant favor for someone, or if someone explicitly owes {user_name}.
        
        Text: "{text_content}"
        
        Respond ONLY with a valid JSON object matching this schema exactly:
        {{
            "is_valid": true or false,
            "owed_by": "Name of the person who owes the favor (or null)",
            "owed_to": "{user_name}",
            "description": "Short description of what the favor was (or null)"
        }}
        Do not use markdown blocks. Return only raw JSON.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
                
            data = json.loads(result_text)
            return data
        except Exception as e:
            logger.error(f"NLP Leveraged failed: {e}")
            return {"is_valid": False}
