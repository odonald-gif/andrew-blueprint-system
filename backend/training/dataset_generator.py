import logging
import json
import os
import requests

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_andrew_dataset(output_file: str = "andrew_dataset.jsonl", num_examples: int = 50):
    """
    Generates synthetic training data for Llama 3 8B.
    It calls the Gemini API to fabricate high-quality Donna-style dialog 
    covering Motion Math, Web Scraping Insights, and Social Leveraging.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("No Gemini API key found to generate synthetic data.")
        return

    # Use the REST API directly to avoid version clashes with pip plugins.
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    
    prompt = f"""
    You are an expert dataset generator. Create {num_examples} variations of an interaction between a User (an IT student) and an autonomous AI named Andrew.
    Andrew is modeled after "Donna Paulsen" from Suits, combined with "Motion AI" logic.
    Andrew is witty, proactive, entirely mathematically logical, but delivers it with supreme confidence and social intelligence.
    
    Output strictly as a JSON array where each element has:
    - instruction: The context or what the user asked. (e.g. "I have a meeting right now but I am exhausted.")
    - output: Andrew's response. (e.g. "You're not tired, you're annoyed. I pushed the meeting to 4 PM and blocked 30 minutes for a double espresso. Take the win.")
    
    Make the outputs dynamic, referencing cloud architect jobs, DAAD scholarships, flutter bugs, or social leverage.
    Do NOT output markdown (no ```json). Output raw JSON array ONLY.
    """

    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    logger.info(f"Generating {num_examples} Synthetic examples for Andrew Brain...")
    
    try:
        response = requests.post(api_url, headers={"Content-Type": "application/json"}, json=data)
        response.raise_for_status()
        
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        
        # Clean potential markdown wrapping randomly outputted by models
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            
        json_data = json.loads(result_text)
        
        # Write to JSONL formatting suitable for HuggingFace / Unsloth
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in json_data:
                # Alpaca/Chat template base structure
                formatted = {
                    "text": f"Instruction: {item['instruction']}\\nResponse: {item['output']}"
                }
                f.write(json.dumps(formatted) + "\\n")
                
        logger.info(f"Successfully generated dataset at {output_file}!")
        
    except Exception as e:
        logger.error(f"Gemini API rate limit hit or failed: {e}. Andrew, debug generation script.")
        raise RuntimeError(f"Failed to generate dataset: {e}")

if __name__ == "__main__":
    # To keep it quick and cheap, we do 50 at a time. The user can loop this to reach 500.
    generate_andrew_dataset("andrew_dataset.jsonl", 50)
