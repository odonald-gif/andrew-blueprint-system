import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class VisionEngine:
    """
    The Multimodal Graphics Department for Andrew.
    Generates professional, agency-quality imagery for LinkedIn and GitHub posts.
    """
    def __init__(self):
        # We look for a dedicated image generation API key (e.g., SiliconFlow, Midjourney, OpenAI)
        self.api_key = os.getenv("IMAGE_GEN_API_KEY", None)

    def _generate_prompt_from_topic(self, topic: str) -> str:
        """Translates a technical topic into a midjourney-style image prompt."""
        # In a full setup, the PersonaEngine would generate this perfectly.
        return f"A high-end, clean, corporate 3D isometric architectural diagram illustrating {topic}, dark mode, glassmorphism, glowing neon accents, unreal engine 5 render, hyper-realistic, 8k resolution --ar 16:9"

    def generate_linkedin_graphic(self, post_topic: str) -> Dict[str, Any]:
        """
        Calls a Text-to-Image API to generate an asset.
        """
        logger.info(f"Vision Engine: Generating professional graphic for topic: {post_topic}")
        image_prompt = self._generate_prompt_from_topic(post_topic)
        
        if not self.api_key:
            raise ValueError("No IMAGE_GEN_API_KEY found in environment.")
            
        try:
            import requests
            response = requests.post(
                 "https://api.siliconflow.cn/v1/image/generate", 
                 json={"prompt": image_prompt, "model": "black-forest-labs/FLUX.1-schnell"},
                 headers={"Authorization": f"Bearer {self.api_key}"}
             )
            
            if response.status_code != 200:
                raise RuntimeError(f"Vision API returned status {response.status_code}: {response.text}")
                
            data = response.json()
            image_url = data.get("images", [{}])[0].get("url", "")
            
            if not image_url:
                raise RuntimeError("Vision API returned successful status but no image URL.")
                
            return {
                "status": "success",
                "image_url": image_url,
                "prompt_used": image_prompt
            }
        except Exception as e:
            logger.error(f"Vision API Error: {e}")
            return {"status": "error", "error": str(e)}

vision_engine = VisionEngine()
