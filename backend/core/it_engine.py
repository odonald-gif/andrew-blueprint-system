import logging
import os
import shutil
import psutil
from core.persona import PersonaEngine

logger = logging.getLogger(__name__)

class ITSuperEngine:
    """
    The IT DevOps Lab & Server Monitor.
    Reads real system metrics instead of returning hardcoded values.
    """
    def __init__(self):
        self.ai = PersonaEngine()

    def generate_network_diagram(self, architecture_desc: str) -> str:
        """Uses Gemini to generate a Mermaid.js network diagram for the given architecture."""
        logger.info(f"Generating Mermaid.js diagram for: {architecture_desc}")
        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=(
                    f"Generate a Mermaid.js graph TD diagram for this architecture: {architecture_desc}\n"
                    f"Return ONLY the mermaid code block, nothing else."
                ),
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Diagram generation failed: {e}")
            return f"Error generating diagram: {e}"

    def check_server_health(self) -> dict:
        """Reads real system metrics using psutil."""
        logger.info("Checking local system health...")
        try:
            disk = shutil.disk_usage("/")
            disk_pct = round((disk.used / disk.total) * 100, 1)
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)

            return {
                "status": "Healthy" if mem.percent < 90 and cpu < 90 else "Stressed",
                "cpu_usage": f"{cpu}%",
                "ram_usage": f"{round(mem.used / (1024**3), 1)}GB / {round(mem.total / (1024**3), 1)}GB",
                "ram_percent": f"{mem.percent}%",
                "disk_usage": f"{disk_pct}%",
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unknown", "error": str(e)}

    def debug_code(self, language: str, error_msg: str) -> str:
        """Uses Gemini to analyze and debug a code error."""
        logger.info(f"Debugging {language} error: {error_msg}")
        try:
            response = self.ai.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=(
                    f"You are a senior {language} engineer. Debug this error:\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Provide a concise diagnosis and fix."
                ),
            )
            return response.text.strip()
        except Exception as e:
            return f"Debug analysis unavailable: {e}"

it_engine = ITSuperEngine()
