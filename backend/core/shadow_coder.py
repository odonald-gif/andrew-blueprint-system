import os
import subprocess
import logging
from typing import List

logger = logging.getLogger("ShadowCoder")

class ShadowCoder:
    """
    Automated Scaffolding Engine.
    When Andrew wins a gig, this module builds the foundation before Donald wakes up.
    """
    def __init__(self, sandbox_dir: str = "sandbox"):
        self.sandbox_dir = sandbox_dir
        if not os.path.exists(self.sandbox_dir):
            os.makedirs(self.sandbox_dir)

    def scaffold_project(self, project_name: str, tech_stack: List[str]):
        """Generates the boilerplate architecture in the sandbox."""
        project_path = os.path.join(self.sandbox_dir, project_name)
        if not os.path.exists(project_path):
            os.makedirs(project_path)

        logger.info(f"Shadow Coder: Scaffolding project '{project_name}' with {tech_stack}")

        if "FastAPI" in tech_stack:
            self._write_fastapi_boilerplate(project_path)
        
        if "React" in tech_stack:
            # Execute npx create-vite if possible, or just mock the package.json for safety
            self._write_react_boilerplate(project_path)

        if "Docker" in tech_stack:
            self._write_dockerfile(project_path)

        # Initialize Git
        try:
            subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
            logger.info("Shadow Coder: Initialized Git repository.")
        except Exception as e:
            logger.error(f"Failed to initialize git: {e}")

        return {"status": "scaffolded", "path": project_path}

    def _write_fastapi_boilerplate(self, path: str):
        main_py = '''from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"status": "ok"}\n'''
        with open(os.path.join(path, "main.py"), "w") as f:
            f.write(main_py)
        with open(os.path.join(path, "requirements.txt"), "w") as f:
            f.write("fastapi\nuvicorn\n")

    def _write_react_boilerplate(self, path: str):
        try:
            logger.info("Shadow Coder: Running npx create-vite...")
            subprocess.run(["npx", "-y", "create-vite", "frontend", "--template", "react"], cwd=path, check=True, capture_output=True)
        except Exception as e:
            logger.error(f"Failed to create React app using npx: {e}")
            raise RuntimeError(f"npx create-vite failed: {e}. Andrew, use Developer Bridge to debug.")

    def _write_dockerfile(self, path: str):
        dockerfile = 'FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]\n'
        with open(os.path.join(path, "Dockerfile"), "w") as f:
            f.write(dockerfile)

shadow_coder = ShadowCoder()
