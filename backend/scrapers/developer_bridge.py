import subprocess
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DeveloperBridge:
    """
    Andrew's connection to the Antigravity IDE.
    
    Three collaboration modes:
    
    1. DIRECT BUILD — Andrew calls Antigravity CLI with a task description,
       Antigravity builds iteratively with its full tool suite (file editing,
       running commands, debugging), and returns the finished code.
    
    2. CONSULT — Andrew asks Antigravity a technical question and gets
       an expert answer back, which Andrew stores as a lesson.
    
    3. REVIEW — Andrew sends code he wrote himself to Antigravity for
       quality review and improvement suggestions.
    
    All code is built in a sandboxed directory.
    Protected branches (main/master) are never pushed to directly.
    """
    def __init__(self, sandbox_dir: str = "./sandbox"):
        self.sandbox_dir = os.path.abspath(sandbox_dir)
        if not os.path.exists(self.sandbox_dir):
            os.makedirs(self.sandbox_dir)

    def _get_andrew_context(self) -> str:
        """Gather roadmap goals, retrospective assessments, and .env keys."""
        context_parts = []
        # .env keys
        try:
            env_keys = []
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        env_keys.append(line.split("=")[0].strip())
            if env_keys:
                context_parts.append(f"Available Environment Variables (use os.getenv): {', '.join(env_keys)}")
        except Exception:
            pass
            
        # Roadmap Goals
        try:
            from core.roadmap_manager import roadmap_manager
            status = roadmap_manager.get_roadmap_status()
            goal = status.get("overall_goal")
            if goal:
                context_parts.append(f"Overall Goal: {goal}")
        except Exception:
            pass
            
        # Retrospective Assessment
        try:
            from db.memory_cortex import memory_cortex
            recent = memory_cortex.get_recent_episodes(limit=50)
            retro = next((ep for ep in recent if ep.get("event_type") == "DAILY_RETROSPECTIVE_COMPLETE"), None)
            if retro:
                context_parts.append(f"Recent Assessment & Adjustments: {retro.get('description')}")
        except Exception:
            pass
            
        if not context_parts:
            return ""
            
        return "\n--- Andrew's Personal Context ---\n" + "\n".join(context_parts) + "\n---------------------------------"

    def trigger_antigravity_build(self, task_description: str) -> Dict[str, Any]:
        """
        Mode 1: DIRECT BUILD.
        Calls the Antigravity CLI to build something from scratch.
        Antigravity has the full iterative loop (edit → run → debug → fix).
        """
        logger.info(f"[DeveloperBridge] Requesting Antigravity build: {task_description[:80]}...")

        andrew_context = self._get_andrew_context()
        enriched_task = f"{task_description}\n{andrew_context}"

        command = [
            "antigravity",
            "--task", enriched_task,
            "--dir", self.sandbox_dir
        ]

        try:
            result = subprocess.run(
                command, capture_output=True, text=True,
                cwd=self.sandbox_dir, timeout=300
            )
            if result.returncode == 0:
                logger.info("[DeveloperBridge] Antigravity build completed successfully.")
                return {"status": "success", "output": result.stdout}
            else:
                logger.warning(f"[DeveloperBridge] Antigravity returned non-zero: {result.stderr[:200]}")
                return {"status": "error", "output": result.stderr}

        except FileNotFoundError:
            logger.warning("[DeveloperBridge] Antigravity CLI not found. Falling back to internal builder.")
            return self._fallback_internal_build(task_description)
        except subprocess.TimeoutExpired:
            return {"status": "error", "output": "Build timed out after 5 minutes."}

    def consult(self, question: str) -> Dict[str, Any]:
        """
        Mode 2: CONSULT.
        Andrew asks a technical architecture question.
        Uses Gemini as a stand-in when Antigravity CLI isn't available.
        """
        logger.info(f"[DeveloperBridge] Consulting on: {question[:80]}...")

        # Try Antigravity CLI first
        command = [
            "antigravity",
            "--task", f"Answer this technical question concisely: {question}",
            "--dir", self.sandbox_dir
        ]

        try:
            result = subprocess.run(
                command, capture_output=True, text=True,
                timeout=120
            )
            if result.returncode == 0:
                return {"status": "success", "answer": result.stdout.strip()}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: use Gemini directly
        try:
            from core.persona import PersonaEngine
            ai = PersonaEngine()
            response = ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=(
                    f"You are a Principal Systems Architect. "
                    f"Answer this concisely and practically:\n\n{question}"
                ),
            )
            return {"status": "success", "answer": response.text.strip(), "source": "gemini_fallback"}
        except Exception as e:
            return {"status": "error", "answer": f"Consultation failed: {e}"}

    def review_code(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Mode 3: REVIEW.
        Andrew sends code he generated to get quality feedback.
        """
        logger.info("[DeveloperBridge] Requesting code review...")

        try:
            from core.persona import PersonaEngine
            ai = PersonaEngine()
            prompt = (
                f"Review this Python code for production readiness. "
                f"Be specific about: bugs, security issues, performance, and missing error handling.\n"
                f"Context: {context}\n\n"
                f"```python\n{code[:3000]}\n```\n\n"
                f"Return a JSON object with: "
                f'{{"score": 1-10, "issues": ["issue1", ...], "suggestions": ["fix1", ...], "verdict": "ship_it" or "needs_work"}}'
                f"\nReturn only raw JSON."
            )

            response = ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )

            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```json")[-1].split("```")[0].strip() if "```json" in text else text.split("```")[1].strip()

            return {"status": "success", "review": json.loads(text)}
        except Exception as e:
            logger.error(f"Code review failed: {e}")
            return {"status": "error", "review": str(e)}

    def push_to_github(self, feature_branch: str, commit_message: str) -> Dict[str, Any]:
        """
        Pushes sandbox code to a GitHub feature branch.
        Protected branches (main/master) are blocked.
        """
        if "main" in feature_branch or "master" in feature_branch:
            logger.warning("Blocked push to protected branch.")
            return {"status": "blocked", "output": "Cannot push to main/master."}

        if not feature_branch.startswith("feature/"):
            feature_branch = f"feature/{feature_branch}"

        logger.info(f"Pushing to {feature_branch}...")

        try:
            subprocess.run(["git", "checkout", "-b", feature_branch], cwd=self.sandbox_dir, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=self.sandbox_dir, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", commit_message], cwd=self.sandbox_dir, check=True, capture_output=True)
            subprocess.run(["git", "push", "-u", "origin", feature_branch], cwd=self.sandbox_dir, check=True, capture_output=True)

            return {
                "status": "success",
                "output": f"Pushed to origin/{feature_branch}. Ready for PR."
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Git failed: {e}")
            return {"status": "error", "output": str(e)}

    def _fallback_internal_build(self, task_description: str) -> Dict[str, Any]:
        """
        When Antigravity CLI isn't installed, fall back to the internal
        iterative code builder (code_reviewer.iterative_build).
        """
        logger.info("[DeveloperBridge] Using internal iterative builder as fallback.")
        try:
            from core.code_reviewer import code_reviewer
            filename = task_description.lower()[:30].replace(" ", "_").replace("/", "_") + ".py"
            result = code_reviewer.iterative_build(task_description, filename)
            return {
                "status": result["status"],
                "output": f"Internal build: {result['status']} after {result['attempts']} attempts.",
                "details": result
            }
        except Exception as e:
            return {"status": "error", "output": f"Internal build failed: {e}"}


# Singleton instance
dev_bridge = DeveloperBridge()
