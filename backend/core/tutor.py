import logging
import os
from typing import Dict, Any, List
from google import genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SkillTutor:
    """
    The Micro-Learning RAG Engine.
    Cross references needed skills. Generates learning materials and quizzes.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("MISSING GEMINI_API_KEY - Skill Tutor cannot boot.")
        self.client = genai.Client()

    def identify_gaps(self, job_description: str, known_skills: List[str]) -> List[str]:
        """Analyzes a job description against known skills to find gaps"""
        prompt = (
            f"Extract the primary technical IT skills required in this job description: '{job_description}'. "
            f"Then, list only the skills that are missing from this known skillset: {', '.join(known_skills)}. "
            f"Return as a comma-separated list."
        )
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return [s.strip() for s in response.text.split(",") if s.strip()]
        except Exception as e:
            logger.error(f"Gemini API error during gap check: {e}")
            raise RuntimeError(f"Gemini API error during gap check: {e}")

    def generate_quiz(self, subject: str) -> Dict[str, Any]:
        """Generates a multiple choice micro-learning quiz for a skill"""
        prompt = (
            f"Create a 3-question Multiple Choice Quiz on the IT topic: '{subject}'. "
            f"Format it exactly as JSON: {{\"questions\": [{{\"q\": \"...\", \"options\": [\"A..\", \"B..\"], \"answer\": \"A\"}}]}}"
        )
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return {"topic": subject, "quiz_data": response.text}
        except Exception as e:
            logger.error(f"Gemini API error during quiz generation: {e}")
            raise RuntimeError(f"Gemini API error during quiz generation: {e}")
