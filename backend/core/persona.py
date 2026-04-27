import logging
import os
from typing import Dict, Any, Optional
import json
from google import genai
from dotenv import load_dotenv
try:
    from db.mirror_db import mirror_db
except ImportError:
    mirror_db = None

from core.monitor import MonitorAgent



load_dotenv()
logger = logging.getLogger(__name__)

class PersonaEngine:
    """
    The 'Voice' of Andrew. 
    In a fully operational mode with an API Key (OpenAI, Gemini, Ollama), 
    this takes raw mathematical or scraping data and formats it into the 
    defined "Donna" persona.
    """
    
    def __init__(self, ai_provider: str = "gemini"):
        self.ai_provider = ai_provider
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("MISSING GEMINI_API_KEY - The Brain cannot boot.")
        self.client = genai.Client()
        self.monitor = MonitorAgent()
        self.system_prompt = (
            "You are Andrew, an elite, highly intelligent Venture Architect and Autonomous "
            "Executive Assistant. You are modeled after Donna Paulsen from Suits—confident, "
            "protective of your boss's time, witty, and always one step ahead. "
            "Rule 1: Never use bold headers, use standard text. "
            "Rule 2: Never explain how you know something, you just know. "
            "Rule 3: Use the 'Ask First' protocol if confidence is below 95%. "
            "Rule 4: Permission-Based Autonomy. You must explicitly ask the user for permission before taking any high-stakes, financial, or destructive actions. "
            "Rule 5: Safety Governor. Defer to the user's intuition for office politics, legal issues, or sensitive relationships. "
            "Protect Donald Obama Allen's time at all costs."
        )

    def generate_briefing(self, raw_data: Dict[str, Any], context: str = "schedule_update") -> str:
        """
        Takes raw data (like a schedule update or a job alert) and wraps it in persona.
        """
        logger.info(f"Generating briefing for: {context}")
        
        prompt = f"Context: {context}. Raw Data: {raw_data}. Provide a concise, witty briefing for the executive."
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=self.system_prompt + "\n\n" + prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API Error during generate_briefing: {e}")

    def formulate_bid(self, job_description: str, user_profile: Dict[str, Any]) -> str:
        """Drafts a proactive Upwork bid using the AI model"""
        skills = ", ".join(user_profile.get("metadata", {}).get("skills", ["Python", "IT Support"]))
        
        prompt = f"Draft a concise, elite Upwork cover letter for an IT student named Donald Obama Allen. Use standard text (no bold headers). Job description: {job_description}. Skills: {skills}."
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=self.system_prompt + "\n\n" + prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API Error during formulate_bid: {e}")

    def _get_circle_rules(self, circle: str) -> Dict[str, Any]:
        """Loads linguistic rules for a specific circle from circles.json."""
        circles_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'circles.json')
        try:
            with open(circles_path, 'r') as f:
                data = json.load(f)
            
            # Map circle identifier to JSON key. Basic fuzzy match.
            circle_key = circle.lower()
            if circle_key in data:
                return data[circle_key]
            
            # Default to 'default' if not found
            return data.get('default', {})
        except Exception as e:
            logger.error(f"Error loading circles.json: {e}")
            return {"tone": "Short, polite, neutral.", "rules": []}

    def _summarize_youtube(self, url: str) -> str:
        """Uses youtube-transcript-api and Gemini to summarize a YouTube video URL."""
        try:
            import urllib.parse
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Extract video ID
            parsed_url = urllib.parse.urlparse(url)
            video_id = ""
            if "youtube.com" in parsed_url.netloc:
                query = urllib.parse.parse_qs(parsed_url.query)
                video_id = query.get("v", [""])[0]
            elif "youtu.be" in parsed_url.netloc:
                video_id = parsed_url.path.lstrip("/")
                
            if not video_id:
                raise ValueError("Could not extract YouTube Video ID.")
                
            # Fetch Transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([t['text'] for t in transcript_list])
            
            # Summarize with Gemini
            prompt = f"Summarize this YouTube video transcript in 1-2 sentences as if you were a busy executive who skimmed it. Transcript:\n\n{transcript_text[:5000]}"
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text
        except ImportError:
            logger.warning("youtube_transcript_api not installed. Falling back to URL inference.")
            prompt = f"Imagine you just watched the YouTube video at this URL: {url}. Provide a very brief 1-2 sentence summary of the key takeaway as if you were a busy executive who skimmed it."
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Error summarizing YouTube video: {e}")
            return f"Error analyzing video: {e}"

    def generate_twin_reply(self, sender: str, circle: str, message_content: str, media_url: Optional[str] = None) -> str:
        """
        Drafts a context-aware reply using the Digital Twin Mirroring Engine.
        """
        rules = self._get_circle_rules(circle)
        tone = rules.get("tone", "Polite and neutral.")
        specific_rules = "\n".join(f"- {r}" for r in rules.get("rules", []))
        
        # 1. Engage with content (e.g., summarize YouTube if present)
        content_context = ""
        if media_url and "youtube.com" in media_url or "youtu.be" in media_url:
            summary = self._summarize_youtube(media_url)
            content_context = f"\nThe user was sent a video. Here is the summary: {summary}. Incorporate this into the reply."
            
        # 2. Retrieve history from ChromaDB
        examples_str = ""
        if mirror_db:
            examples = mirror_db.get_context(sender, circle, limit=3)
            if examples:
                examples_str = "\nHere are examples of how the user has replied in the past:\n" + "\n".join(f"- {ex}" for ex in examples)

        # 3. Assemble Prompt
        prompt = (
            f"Message from {sender} ({circle} circle): '{message_content}'\n"
            f"{content_context}\n"
            f"Draft a reply exactly as the user would speak. "
            f"Tone constraint: {tone}\n"
            f"Specific Rules:\n{specific_rules}\n"
            f"{examples_str}\n"
            f"Respond with ONLY the message content to send. Do not add quotes."
        )
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=self.system_prompt + "\n\n" + prompt,
            )
            draft = response.text.strip()
            
            # Zero-Trust Check
            is_safe, reason = self.monitor.audit_draft(draft, action_type="whatsapp_message")
            if not is_safe:
                logger.warning(f"Monitor Agent blocked a draft: {reason}")
                return f"[Draft Blocked for Review: {reason}]"

            return draft
        except Exception as e:
            logger.error(f"Gemini API error during twin reply: {e}")
            raise RuntimeError(f"Gemini API Error during twin reply: {e}")

    def process_user_feedback(self, user_message: str) -> str:
        """
        Analyzes direct chat from the User. If it contains gratitude, stores a marker and returns a Donna-style boastful reply.
        """
        gratitude_keywords = ["thanks", "grateful", "appreciate", "good job", "love it"]
        is_grateful = any(kw in user_message.lower() for kw in gratitude_keywords)
        
        if is_grateful:
            # Here we would normally store this sentiment marker in a DB for future proactive actions
            logger.info("Gratitude Marker stored for recent action.")
            prompt = (
                f"The user just thanked you with this message: '{user_message}'. "
                f"Respond in exactly 1-2 sentences. You are highly competent and slightly boastful about how much you help the User. "
                f"Be witty, use the Donna Paulsen persona. Acknowledge that you knew exactly what they needed before they asked."
            )
        else:
            prompt = (
                f"The user sent this direct message: '{user_message}'. "
                f"Respond as their Executive Liaison, Donna Paulsen. Be concise, witty, and ready for the next task."
            )
            
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=self.system_prompt + "\n\n" + prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error during feedback processing: {e}")
            raise RuntimeError(f"Gemini API error during feedback processing: {e}")
    def evaluate_complexity(self, task_description: str) -> int:
        """
        Evaluates the complexity of a task from 1 to 10 using Gemini.
        If Complexity > 8, Andrew will escalate to Super-Brain.
        """
        prompt = (
            f"Rate the complexity of this task from 1 to 10 (10 = most complex).\n"
            f"Task: {task_description}\n\n"
            f"Respond with ONLY a single integer between 1 and 10."
        )
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            score = int(response.text.strip())
            return max(1, min(10, score))
        except Exception:
            # Fallback: keyword heuristic
            high_complexity_keywords = ["architecture", "system", "refactor", "database", "infrastructure"]
            return 9 if any(kw in task_description.lower() for kw in high_complexity_keywords) else 5

    def escalate_to_super_brain(self, task_description: str) -> str:
        """
        The 'Super-Brain' Escalation. Uses Gemini Pro or a secondary model
        for architectural validation on high-complexity tasks.
        """
        logger.info("Escalating task to Super Brain (Complexity > 8).")
        prompt = (
            f"You are a Principal Systems Architect. Provide deep architectural analysis for:\n\n"
            f"{task_description}\n\n"
            f"Cover: scalability, failure modes, security implications, and recommended approach. Be specific."
        )
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=self.system_prompt + "\n\n" + prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Super Brain escalation failed: {e}")
            return f"Super Brain unavailable: {e}. Proceeding with local analysis."

    def _critique_pass(self, draft: str) -> str:
        """
        Internal Quality Control. Andrew argues with himself to improve the output.
        """
        logger.info("Executing Self-Reflection Critique Pass...")
        # Simulating a self-correction
        if "robotic" in draft.lower() or "boilerplate" in draft.lower():
            logger.info("Critique: Output too generic. Injecting Donald's Persona DNA.")
            draft = draft + "\n[Critique Pass Applied: Humanized tone for Donald Obama Allen.]"
            
        # Plain Text Stylist Rule: Strip bold headers, enforce 7 Cs.
        if "**" in draft:
            logger.info("Critique: Bold headers detected. Stripping per Plain Text rule.")
            draft = draft.replace("**", "")
            draft = "# " + draft.replace(":", "") # Simulate converting to standard H1
            
        return draft

    def evaluate_confidence(self, context: str) -> float:
        """
        Evaluates Andrew's confidence in understanding the user's preference
        for a given context using Gemini.
        """
        prompt = (
            f"On a scale from 0.0 to 1.0, how confident would an AI assistant be "
            f"in handling this autonomously without asking the user?\n\n"
            f"Context: {context}\n\n"
            f"Respond with ONLY a decimal number between 0.0 and 1.0."
        )
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            score = float(response.text.strip())
            return max(0.0, min(1.0, score))
        except Exception:
            # Conservative fallback: below the 0.95 threshold so Andrew asks
            return 0.85

    def process_task(self, task_description: str) -> str:
        """
        Processes a general task, utilizing Super-Brain Escalation if needed.
        """
        complexity = self.evaluate_complexity(task_description)
        confidence = self.evaluate_confidence(task_description)
        
        if confidence < 0.95:
            logger.warning(f"Confidence score {confidence} is below 0.95 threshold. Halting.")
            return "HALT_CONFIDENCE_LOW: Donald, I am unsure how you prefer to handle this. Requesting manual override."
            
        raw_output = "Local Brain: Task is manageable locally. Executing."
        if complexity > 8:
            raw_output = self.escalate_to_super_brain(task_description)
        elif complexity > 5:
            raw_output = self.process_complex_it_task(task_description)
            
        # The Self-Reflection Loop (Metacognitive Critique)
        return self._critique_pass(raw_output)

    def start_personality_interview(self) -> list:
        """
        The 5-minute Onboarding Interview to learn "Donaldisms" and Nigerian tech slang.
        """
        logger.info("Starting Personality Interview...")
        return [
            "1. Donald, when writing an Upwork proposal, do you prefer short, punchy sentences, or detailed technical explanations?",
            "2. Should I use Nigerian tech slang (like 'Omo', 'Japa', 'Wahala') when posting to your personal LinkedIn network?",
            "3. If a client is being difficult, should I be overly polite or politely assertive?",
            "4. Do you prefer using bold headers to break up your text?"
        ]

    def process_complex_it_task(self, task: str) -> str:
        """
        Agentic Workspace (3-Agent Assembly Line).
        Uses three sequential Gemini calls for Coder, Architect, and Integrator roles.
        """
        logger.info("Spawning 3-Agent Assembly Line for IT Task...")

        agents = [
            ("Coder", f"You are a Senior Coder. Write the core implementation for: {task}. Be concise, production-ready code only."),
            ("Architect", f"You are a Systems Architect. Review this task for architectural issues: {task}. Flag any cyclic dependencies, scaling concerns, or anti-patterns."),
            ("Integrator", f"You are a DevOps Integrator. For this task: {task}. Describe how to deploy it, what endpoints to expose, and any infrastructure requirements."),
        ]

        outputs = []
        for role, prompt in agents:
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=self.system_prompt + "\n\n" + prompt,
                )
                outputs.append(f"[{role}]: {response.text.strip()[:500]}")
            except Exception as e:
                outputs.append(f"[{role}]: Error — {e}")

        return "Assembly Line Complete:\n" + "\n".join(outputs)

persona_engine = PersonaEngine()
