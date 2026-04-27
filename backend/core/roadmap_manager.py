import json
import os
import logging
from typing import Dict, List, Any

logger = logging.getLogger("RoadmapManager")

class RoadmapManager:
    """
    Manages Andrew's long-term evolution goals and tracking.
    Outputs data formatted for a frontend Progress Bar.
    """
    def __init__(self, storage_path: str = "data/roadmap.json"):
        self.storage_path = storage_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.storage_path):
            default_roadmap = {
                "overall_goal": "$100,000 / Month Autonomous Income",
                "progress_percentage": 0,
                "milestones": [
                    {
                        "id": "m1",
                        "title": "Establish Coinbase CDP Sovereign Wallet",
                        "status": "completed",
                        "weight": 10
                    },
                    {
                        "id": "m2",
                        "title": "Automated YouTube Content Empire",
                        "status": "completed",
                        "weight": 20
                    },
                    {
                        "id": "m3",
                        "title": "Meta-Coder Self-Evolution Loop",
                        "status": "in_progress",
                        "weight": 30
                    },
                    {
                        "id": "m4",
                        "title": "Arbitrage Outbound Engine",
                        "status": "pending",
                        "weight": 40
                    }
                ]
            }
            self._save(default_roadmap)

    def _load(self) -> dict:
        with open(self.storage_path, "r") as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=4)

    def get_roadmap_status(self) -> dict:
        """Calculates current progress and returns the roadmap."""
        data = self._load()
        
        total_weight = sum(m["weight"] for m in data["milestones"])
        completed_weight = sum(m["weight"] for m in data["milestones"] if m["status"] == "completed")
        
        progress = 0
        if total_weight > 0:
            progress = int((completed_weight / total_weight) * 100)
            
        data["progress_percentage"] = progress
        self._save(data)
        
        logger.info(f"Roadmap checked. Current Progress: {progress}%")
        return data

    def update_milestone_status(self, milestone_id: str, new_status: str):
        """Allows Andrew to mark tasks as completed as he evolves."""
        data = self._load()
        for m in data["milestones"]:
            if m["id"] == milestone_id:
                m["status"] = new_status
                logger.info(f"Milestone {milestone_id} updated to {new_status}")
                break
        self._save(data)

roadmap_manager = RoadmapManager()
