import logging
from core.persona import PersonaEngine
from core.api_pool import api_pool

logger = logging.getLogger(__name__)

class LearningEngine:
    """
    The Personal Professor (Skill Ascension Engine).
    Uses Gemini to generate real micro-lessons, quizzes, and assessments
    on any topic. Andrew also uses this to teach himself new skills.
    """
    def __init__(self):
        self.ai = PersonaEngine()

    def generate_micro_lesson(self, topic: str) -> str:
        """
        Generates a 10-minute micro-lesson on any topic using Gemini.
        """
        logger.info(f"Generating Micro-Lesson for topic: {topic}")

        account = api_pool.acquire("gemini_calls", preferred_role="brain")
        if account is None:
            return f"[Quota exhausted] Cannot generate lesson for: {topic}"

        prompt = (
            f"Create a concise, expert-level 10-minute micro-lesson on: {topic}.\n\n"
            f"Structure it as:\n"
            f"1. Why this matters (2 sentences)\n"
            f"2. Core concept explained simply (3-4 sentences)\n"
            f"3. A practical example or code snippet\n"
            f"4. One actionable next step to practice this\n\n"
            f"Target audience: a motivated developer/entrepreneur leveling up."
        )

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Micro-lesson generation failed: {e}")
            return f"Lesson generation failed for '{topic}': {e}"

    def generate_quiz(self, topic: str) -> dict:
        """
        Generates a real quiz question with multiple choice answers using Gemini.
        """
        logger.info(f"Generating Quiz for topic: {topic}")

        account = api_pool.acquire("gemini_calls", preferred_role="brain")
        if account is None:
            return {"error": "No Gemini quota for quiz generation"}

        prompt = (
            f"Generate a challenging but fair multiple-choice quiz question about: {topic}.\n\n"
            f"Return ONLY a JSON object with these keys:\n"
            f"- \"question\": the question text\n"
            f"- \"options\": array of 4 possible answers\n"
            f"- \"answer\": the correct answer (must be one of the options)\n"
            f"- \"explanation\": 1-2 sentence explanation of why\n\n"
            f"No markdown blocks. Return raw JSON only."
        )

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            import json
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```json")[-1].split("```")[0].strip() if "```json" in text else text.split("```")[1].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return {"error": f"Quiz generation failed: {e}"}

    def assess_skill_level(self, topic: str) -> dict:
        """
        Assesses the user's current skill level on a topic by generating
        a short diagnostic question set.
        """
        account = api_pool.acquire("gemini_calls", preferred_role="brain")
        if account is None:
            return {"status": "no_quota"}

        prompt = (
            f"Generate a 3-question skill assessment for: {topic}.\n"
            f"Include 1 beginner, 1 intermediate, and 1 advanced question.\n"
            f"Return as a JSON array of objects with: question, difficulty, options (4 each), answer.\n"
            f"No markdown. Raw JSON only."
        )

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            import json
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```json")[-1].split("```")[0].strip() if "```json" in text else text.split("```")[1].strip()
            questions = json.loads(text)
            return {"status": "assessment_ready", "questions": questions}
        except Exception as e:
            logger.error(f"Assessment generation failed: {e}")
            return {"status": "error", "reason": str(e)}

    def draft_self_improvement(self) -> dict:
        """
        Andrew's self-improvement loop.
        Uses Gemini to analyze the codebase for bottlenecks and propose fixes.
        """
        logger.info("Initiating Self-Improvement Code Analysis...")

        account = api_pool.acquire("gemini_calls", preferred_role="research")
        if account is None:
            return {"status": "no_quota"}

        prompt = (
            "You are Andrew's internal code quality analyst. "
            "Identify ONE specific, actionable improvement to make in an autonomous agent system. "
            "Focus on: performance bottlenecks, error handling gaps, or missing async patterns. "
            "Return a JSON object with: target_file, issue_detected, proposed_fix, priority (1-10).\n"
            "No markdown. Raw JSON only."
        )

        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            import json
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```json")[-1].split("```")[0].strip() if "```json" in text else text.split("```")[1].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Self-improvement analysis failed: {e}")
            return {"status": "error", "reason": str(e)}

learning_engine = LearningEngine()
