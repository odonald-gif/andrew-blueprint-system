import logging
import os
import requests
from typing import List

logger = logging.getLogger("VideoFactory")

class VideoFactory:
    """
    Automated Video Production Engine.
    Stitches generated audio, stock footage, and text into an MP4 file.
    """
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVEN_LABS_API_KEY", os.getenv("ELEVENLABS_API_KEY"))
        self.voice_id = os.getenv("ELEVEN_LABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.pexels_api_key = os.getenv("PEXELS_API_KEY") # Optional, for real stock footage

    def generate_audio(self, narration_text: str, output_path: str) -> bool:
        """Generates TTS using ElevenLabs"""
        if not self.elevenlabs_api_key:
            logger.error("No ElevenLabs API Key. Cannot generate video narration.")
            return False
            
        logger.info("Generating narration via ElevenLabs...")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        data = {
            "text": narration_text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                logger.error(f"ElevenLabs Error: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Audio Generation Error: {e}")
            return False

    def fetch_stock_video(self, query: str, output_path: str) -> bool:
        """Fetches a free stock video from Pexels API"""
        if not self.pexels_api_key:
            logger.warning("No Pexels API Key. Using fallback static visual generation.")
            return False
            
        logger.info(f"Fetching stock footage for: {query}")
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
        headers = {"Authorization": self.pexels_api_key}
        
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                videos = res.json().get("videos", [])
                if videos and videos[0]["video_files"]:
                    # Get the HD link
                    video_url = videos[0]["video_files"][0]["link"]
                    video_res = requests.get(video_url, stream=True)
                    with open(output_path, 'wb') as f:
                        for chunk in video_res.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                    return True
        except Exception as e:
            logger.error(f"Pexels fetch error: {e}")
            
        return False

    def build_video(self, script_data: dict, output_filename: str = "output.mp4") -> dict:
        """
        Orchestrates the creation of the video.
        Requires 'moviepy' library (pip install moviepy).
        """
        try:
            import moviepy.editor as mp
        except ImportError:
            logger.error("moviepy is not installed. Run 'pip install moviepy'.")
            return {"status": "error", "message": "moviepy missing"}

        logger.info("Initializing Video Assembly...")
        
        # In a full implementation, we parse the script_data['script'] for [NARRATION] and [SCENE].
        # For MVP, we pass the entire script to TTS.
        full_text = script_data.get("script", "Welcome to another video.")
        audio_path = "tmp/narration.mp3"
        video_path = "tmp/bg_video.mp4"
        
        if not os.path.exists("tmp"):
            os.makedirs("tmp")

        # 1. Generate Audio
        success = self.generate_audio(full_text, audio_path)
        if not success:
            return {"status": "error", "message": "Audio generation failed."}

        # 2. Get Video
        video_success = self.fetch_stock_video("technology abstract", video_path)
        
        try:
            audio_clip = mp.AudioFileClip(audio_path)
            
            if video_success:
                video_clip = mp.VideoFileClip(video_path)
                # Loop video if shorter than audio
                if video_clip.duration < audio_clip.duration:
                    import math
                    loops = math.ceil(audio_clip.duration / video_clip.duration)
                    video_clip = mp.concatenate_videoclips([video_clip] * loops)
                
                # Trim to audio length
                video_clip = video_clip.subclip(0, audio_clip.duration)
            else:
                # Fallback: Create a static black ColorClip if no stock video
                video_clip = mp.ColorClip(size=(1920, 1080), color=(20, 20, 20), duration=audio_clip.duration)

            # Set the audio
            final_clip = video_clip.set_audio(audio_clip)
            
            # Optional: Add Text Overlay for Title
            # txt_clip = mp.TextClip(script_data.get("title", "Automated Video"), fontsize=70, color='white')
            # txt_clip = txt_clip.set_position('center').set_duration(5)
            # final_clip = mp.CompositeVideoClip([final_clip, txt_clip])

            final_path = os.path.join("data", output_filename)
            if not os.path.exists("data"):
                os.makedirs("data")
                
            logger.info("Rendering final MP4...")
            final_clip.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
            
            return {"status": "success", "file_path": final_path}
            
        except Exception as e:
            logger.error(f"Video rendering error: {e}")
            return {"status": "error", "message": str(e)}

video_factory = VideoFactory()
