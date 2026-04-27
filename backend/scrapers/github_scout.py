import requests
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class GitHubScout:
    """
    Scans the GitHub REST API for trending repositories and open-source projects.
    Filters for relevant 'Japa Engine' tech (Cloud, DevOps, AI, Python) and injects them
    into Donald's Learning Queue.
    """
    def __init__(self):
        self.base_url = "https://api.github.com/search/repositories"
        self.keywords = ["kubernetes", "docker", "generative-ai", "fastapi"]
        
    def find_trending_projects(self, language: str = "python", limit: int = 3) -> List[Dict[str, Any]]:
        """
        Uses GitHub's Search API to find high-impact repos created or updated recently.
        """
        logger.info(f"Scanning GitHub for trending {language} projects...")
        
        # Build query for highly starred, recently active repos
        query = f"language:{language} stars:>1000"
        
        try:
            params = {
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": limit
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            items = response.json().get("items", [])
            valid_projects = []
            
            for item in items:
                valid_projects.append({
                    "name": item["name"],
                    "url": item["html_url"],
                    "description": item["description"],
                    "stars": item["stargazers_count"]
                })
                
            return valid_projects
        except Exception as e:
            logger.error(f"GitHub Scout failed to retrieve data: {e}")
            return []

if __name__ == "__main__":
    scout = GitHubScout()
    trends = scout.find_trending_projects()
    print("Trending GitHub Projects for the Learning Queue:")
    print(json.dumps(trends, indent=2))
