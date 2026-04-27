import os
import subprocess
import logging
import shutil
import ast
from typing import Dict, Any, Optional
from core.persona import PersonaEngine
from core.black_book import BlackBook
from core.api_pool import api_pool

logger = logging.getLogger("CodeReviewer")

class CodeReviewer:
    """
    The Sandbox Protocol + Iterative Build Loop.
    
    Instead of one-shot code generation, Andrew can now:
    1. Generate code via Gemini
    2. Test it in the sandbox
    3. Read the error if it fails
    4. Feed the error back to Gemini and try again
    5. Repeat up to MAX_RETRIES times
    6. Store successful patterns in BlackBook for future learning
    """
    MAX_RETRIES = 5

    def __init__(self, sandbox_dir: str = "sandbox", core_dir: str = "core"):
        self.sandbox_dir = sandbox_dir
        self.core_dir = core_dir
        self.ai = PersonaEngine()
        self.memory = BlackBook()

        if not os.path.exists(self.sandbox_dir):
            os.makedirs(self.sandbox_dir)

    # ── Sandbox File Operations ──────────────────────────────────

    def write_to_sandbox(self, filename: str, code_content: str) -> str:
        """Writes untrusted code to the sandbox directory."""
        filepath = os.path.join(self.sandbox_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_content)
        logger.info(f"Wrote code to sandbox: {filepath}")
        return filepath

    def run_tests(self, filepath: str) -> Dict[str, Any]:
        """
        Runs syntax check + import test on sandbox file.
        Returns {"passed": bool, "error": str or None}
        """
        logger.info(f"Running sandbox tests on {filepath}...")

        # 1. Python syntax check (AST parse — no execution)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            ast.parse(source)
        except SyntaxError as e:
            error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
            logger.error(f"Syntax check failed: {error_msg}")
            return {"passed": False, "error": error_msg}

        # 2. Compile check (catches more subtle issues)
        try:
            subprocess.run(
                ["python", "-m", "py_compile", filepath],
                check=True, capture_output=True, text=True, timeout=30
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip()
            logger.error(f"Compile check failed: {error_msg}")
            return {"passed": False, "error": error_msg}
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Compilation timed out after 30s"}

        # 3. Import test (catches runtime-level crashes)
        try:
            module_name = os.path.basename(filepath).replace(".py", "")
            subprocess.run(
                ["python", "-c", f"import sys; sys.path.insert(0, '{self.sandbox_dir}'); import {module_name}"],
                check=True, capture_output=True, text=True, timeout=30
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip()
            logger.error(f"Import test failed: {error_msg}")
            return {"passed": False, "error": error_msg}
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Import test timed out after 30s"}

        logger.info(f"All sandbox tests PASSED for {filepath}")
        return {"passed": True, "error": None}

    def merge_to_core(self, filename: str) -> dict:
        """Moves verified code from sandbox to core directory."""
        sandbox_path = os.path.join(self.sandbox_dir, filename)
        core_path = os.path.join(self.core_dir, filename)

        if not os.path.exists(sandbox_path):
            return {"status": "error", "message": "File not found in sandbox."}

        try:
            shutil.copy2(sandbox_path, core_path)
            logger.info(f"CODE MERGED: {filename} → {core_path}")
            return {"status": "merged", "path": core_path}
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            return {"status": "error", "message": str(e)}

    # ── Iterative Build Loop ─────────────────────────────────────

    def iterative_build(self, task_description: str, filename: str) -> Dict[str, Any]:
        """
        The core iteration loop. Before writing any code, Andrew consults
        the Antigravity IDE for architecture guidance, then:
        1. Generates code informed by the consultation
        2. Tests it in sandbox
        3. If it fails, feeds the error back for another attempt
        4. Repeats up to MAX_RETRIES times
        5. Stores successful patterns for future learning
        """
        logger.info(f"Starting iterative build: {task_description}")

        account = api_pool.acquire("gemini_calls", preferred_role="worker")
        if account is None:
            return {"status": "no_quota", "attempts": 0}

        # ── Step 0: Consult Antigravity for architecture guidance ──
        consultation = self._consult_before_building(task_description)
        logger.info(f"Consultation complete. Proceeding with guided build.")

        history = []  # Track attempts for learning
        last_error = None
        code_content = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info(f"Build attempt {attempt}/{self.MAX_RETRIES}")

            # Generate or fix code — first attempt uses consultation context
            if attempt == 1:
                code_content = self._generate_initial(task_description, consultation)
            else:
                code_content = self._fix_from_error(task_description, code_content, last_error, attempt)

            if not code_content:
                history.append({"attempt": attempt, "result": "generation_failed"})
                continue

            # Write to sandbox and test
            filepath = self.write_to_sandbox(filename, code_content)
            test_result = self.run_tests(filepath)

            history.append({
                "attempt": attempt,
                "result": "passed" if test_result["passed"] else "failed",
                "error": test_result.get("error")
            })

            if test_result["passed"]:
                logger.info(f"Build succeeded on attempt {attempt}!")

                # Store the successful pattern for future learning
                self._store_success_pattern(task_description, code_content, attempt)

                return {
                    "status": "success",
                    "attempts": attempt,
                    "filepath": filepath,
                    "history": history
                }
            else:
                last_error = test_result["error"]
                logger.warning(f"Attempt {attempt} failed: {last_error}")

        # All attempts exhausted
        logger.error(f"Build failed after {self.MAX_RETRIES} attempts.")
        return {
            "status": "failed",
            "attempts": self.MAX_RETRIES,
            "last_error": last_error,
            "history": history
        }

    def _get_andrew_context(self) -> str:
        """Gather roadmap goals, retrospective assessments, and .env keys."""
        context_parts = []
        
        # 1. Available .env keys
        try:
            env_keys = []
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        env_keys.append(line.split("=")[0].strip())
            if env_keys:
                context_parts.append(f"Available Environment Variables (use os.getenv): {', '.join(env_keys)}")
        except Exception as e:
            logger.warning(f"Could not load .env keys for context: {e}")

        # 2. Roadmap Goals
        try:
            from core.roadmap_manager import roadmap_manager
            status = roadmap_manager.get_roadmap_status()
            goal = status.get("overall_goal")
            if goal:
                context_parts.append(f"Overall Goal: {goal}")
        except Exception:
            pass
            
        # 3. Retrospective Assessment
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
            
        return "\n--- Andrew's Personal Context ---\n" + "\n".join(context_parts) + "\n---------------------------------\n"

    def _consult_before_building(self, task_description: str) -> str:
        """
        Step 0 of every build: consult Antigravity IDE for architecture guidance.
        Returns the consultation answer to be used as build context.
        Stores the advice in BlackBook so Andrew compounds knowledge.
        """
        logger.info(f"[Consult] Asking Antigravity IDE for architecture guidance...")

        try:
            from scrapers.developer_bridge import dev_bridge
            andrew_context = self._get_andrew_context()
            question = (
                f"I need to build a Python module for: {task_description}\n\n"
                f"{andrew_context}\n"
                f"Before I write any code, give me:\n"
                f"1. The right architecture pattern to use\n"
                f"2. Key classes/functions I should define\n"
                f"3. Edge cases and error handling I must cover\n"
                f"4. Any Python libraries I should use\n"
                f"Be specific and practical — this will directly guide my implementation."
            )
            result = dev_bridge.consult(question)

            if result.get("status") == "success":
                advice = result["answer"]
                # Store as a lesson so Andrew learns architecture patterns over time
                self.memory.log_lesson(
                    "ArchitectureConsult",
                    f"Consulted on '{task_description[:60]}': {advice[:200]}"
                )
                logger.info("[Consult] Received architecture guidance. Stored as lesson.")
                return advice
            else:
                logger.warning("[Consult] Consultation returned no useful answer.")
                return ""
        except Exception as e:
            logger.warning(f"[Consult] Consultation failed (proceeding without): {e}")
            return ""

    def _generate_initial(self, task_description: str, consultation: str = "") -> Optional[str]:
        """Generate the first attempt at code, informed by consultation context."""

        consultation_block = ""
        if consultation:
            consultation_block = (
                f"\n\nArchitecture guidance from senior engineer:\n"
                f"---\n{consultation[:2000]}\n---\n"
                f"Follow this guidance closely in your implementation.\n"
            )

        andrew_context = self._get_andrew_context()
        prompt = (
            f"Write a complete, production-ready Python module for the following task:\n\n"
            f"{task_description}\n"
            f"{andrew_context}\n"
            f"{consultation_block}\n"
            f"Requirements:\n"
            f"- Must be a complete, importable Python file\n"
            f"- Include proper error handling and logging\n"
            f"- No placeholder or mock logic — real implementation only\n"
            f"- Use type hints\n"
            f"- Wrap the code in ```python ... ``` blocks\n"
        )
        return self._call_gemini_for_code(prompt)

    def _fix_from_error(self, task: str, broken_code: str, error: str, attempt: int) -> Optional[str]:
        """Feed the error back to Gemini and ask for a fix."""
        prompt = (
            f"The following Python code was generated for this task:\n"
            f"Task: {task}\n\n"
            f"Code:\n```python\n{broken_code}\n```\n\n"
            f"It failed with this error:\n{error}\n\n"
            f"This is fix attempt {attempt}. Please fix the code and return the COMPLETE "
            f"corrected file. Do not explain — just return the fixed code in ```python ... ``` blocks."
        )
        return self._call_gemini_for_code(prompt)

    def _call_gemini_for_code(self, prompt: str) -> Optional[str]:
        """Call Gemini and extract Python code from the response."""
        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            raw = response.text.strip()
            return self._extract_code(raw)
        except Exception as e:
            logger.error(f"Gemini code generation failed: {e}")
            return None

    def _extract_code(self, raw_text: str) -> Optional[str]:
        """Extract Python code from markdown code blocks."""
        if "```python" in raw_text:
            return raw_text.split("```python")[1].split("```")[0].strip()
        elif "```" in raw_text:
            parts = raw_text.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        # If no code blocks, assume the whole response is code
        if raw_text.startswith(("import ", "from ", "class ", "def ", "#")):
            return raw_text
        return None

    def _store_success_pattern(self, task: str, code: str, attempts: int):
        """Store successful build patterns so Andrew learns over time."""
        # Extract what type of module was built (first 100 chars of task)
        summary = f"Built in {attempts} attempt(s): {task[:100]}"
        self.memory.log_lesson("CodeBuild", summary)

        # Store the code signature (imports + class/function names) for pattern matching
        try:
            tree = ast.parse(code)
            signatures = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    signatures.append(f"class {node.name}")
                elif isinstance(node, ast.FunctionDef):
                    signatures.append(f"def {node.name}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        signatures.append(f"import {alias.name}")

            if signatures:
                pattern = f"Pattern for '{task[:50]}': {', '.join(signatures[:10])}"
                self.memory.log_lesson("CodePattern", pattern)
        except Exception:
            pass  # Pattern extraction is best-effort

code_reviewer = CodeReviewer()
