import sqlite3
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class MemoryCortex:
    """
    The True Memory Cortex of Andrew.
    A hybrid architecture:
    1. SQLite for Temporal/Episodic Memory (Events with timestamps).
    2. ChromaDB for Semantic/Procedural Memory (Vector search of preferences and facts).
    Features a 'Decay Engine' to prune irrelevant old memories.
    """
    def __init__(self, db_dir: str = "data/memory"):
        self.db_dir = db_dir
        os.makedirs(self.db_dir, exist_ok=True)
        
        self.sqlite_path = os.path.join(self.db_dir, "episodic_memory.db")
        self.chroma_path = os.path.join(self.db_dir, "semantic_memory")
        
        self._init_sqlite()
        self._init_chroma()

    def _init_sqlite(self):
        """Initializes the temporal memory ledger."""
        conn = sqlite3.connect(self.sqlite_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                description TEXT,
                decay_score REAL,
                archived INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Episodic Memory (SQLite) initialized.")

    def _init_chroma(self):
        """Initializes the vector memory for semantic search."""
        if not CHROMA_AVAILABLE:
            logger.warning("ChromaDB not installed. Semantic memory offline.")
            self.chroma_client = None
            self.collection = None
            return
            
        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(name="andrew_semantic_cortex")
            logger.info("Semantic Memory (ChromaDB) initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None

    def record_episode(self, event_type: str, description: str, initial_importance: float = 1.0):
        """
        Records a temporal event. 
        initial_importance: 0.0 to 1.0. Higher means it decays slower.
        """
        timestamp = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.sqlite_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO episodes (timestamp, event_type, description, decay_score, archived)
            VALUES (?, ?, ?, ?, 0)
        ''', (timestamp, event_type, description, initial_importance))
        conn.commit()
        conn.close()
        logger.info(f"Recorded Episode: [{event_type}] {description}")

    def add_semantic_knowledge(self, knowledge_id: str, content: str, metadata: Dict[str, Any] = None):
        """
        Stores procedural or semantic facts (e.g., preferences, rules) into ChromaDB.
        """
        if not self.collection:
            logger.warning("Cannot add semantic knowledge. ChromaDB offline.")
            return
            
        metadata = metadata or {}
        metadata["timestamp"] = datetime.utcnow().isoformat()
        
        try:
            self.collection.upsert(
                documents=[content],
                metadatas=[metadata],
                ids=[knowledge_id]
            )
            logger.info(f"Stored Semantic Knowledge: {knowledge_id}")
        except Exception as e:
            logger.error(f"Failed to store semantic knowledge: {e}")

    def retrieve_relevant_knowledge(self, query: str, n_results: int = 3) -> List[str]:
        """
        Finds the most semantically relevant facts or preferences for a given query.
        """
        if not self.collection:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            # results["documents"] is a list of lists
            docs = results.get("documents", [[]])[0]
            return docs
        except Exception as e:
            logger.error(f"Failed to retrieve semantic knowledge: {e}")
            return []

    def run_decay_engine(self):
        """
        The Decay Engine (Tier 2).
        Calculates exponential decay on episodic memories. 
        If a memory's decay_score drops below a threshold, it is archived.
        """
        logger.info("Running Memory Decay Engine...")
        conn = sqlite3.connect(self.sqlite_path)
        c = conn.cursor()
        
        # We define a simple decay logic: score reduces by 10% per day since timestamp
        now = datetime.utcnow()
        
        c.execute("SELECT id, timestamp, decay_score FROM episodes WHERE archived = 0")
        rows = c.fetchall()
        
        archived_count = 0
        for row in rows:
            ep_id, ts_str, current_score = row
            try:
                ts = datetime.fromisoformat(ts_str)
                days_old = (now - ts).days
                if days_old > 0:
                    # Decay formula: new_score = current_score * (0.90 ^ days_old)
                    new_score = current_score * (0.90 ** days_old)
                    
                    if new_score < 0.1:
                        # Archive it
                        c.execute("UPDATE episodes SET archived = 1, decay_score = ? WHERE id = ?", (new_score, ep_id))
                        archived_count += 1
                    else:
                        c.execute("UPDATE episodes SET decay_score = ? WHERE id = ?", (new_score, ep_id))
            except Exception as e:
                logger.error(f"Error processing decay for episode {ep_id}: {e}")
                
        conn.commit()
        conn.close()
        logger.info(f"Decay Engine Complete. Archived {archived_count} old episodic memories.")

    def get_recent_episodes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent, active (unarchived) episodic memories."""
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM episodes WHERE archived = 0 ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

memory_cortex = MemoryCortex()
