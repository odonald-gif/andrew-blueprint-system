import chromadb
from chromadb.config import Settings
import os

class MirrorDB:
    def __init__(self, db_path="data/chroma_db"):
        os.makedirs(db_path, exist_ok=True)
        # Initialize local ChromaDB client
        self.client = chromadb.PersistentClient(path=db_path)
        # Create or get the collection for storing chat history
        self.collection = self.client.get_or_create_collection(
            name="andrew_mirror_history",
            metadata={"hnsw:space": "cosine"}
        )

    def save_interaction(self, sender: str, circle: str, message: str, reply: str):
        """
        Saves a past interaction so Andrew can retrieve it later for mimicking.
        """
        # Generate a unique ID for this interaction
        interaction_id = f"{sender}_{hash(message)}"
        
        # We store the reply as the document so we know *how* the user speaks.
        # We use the incoming message as metadata context.
        self.collection.add(
            documents=[reply],
            metadatas=[{"sender": sender, "circle": circle, "trigger_message": message}],
            ids=[interaction_id]
        )

    def get_context(self, sender: str, circle: str, limit: int = 5) -> list[str]:
        """
        Retrieves the last N interactions for a specific sender/circle to inject into the LLM prompt.
        Because we don't have embeddings for search queries directly yet (we could embed the incoming message),
        we'll just fetch by metadata filter for simplicity in the RAG pipeline.
        """
        try:
            # Get documents for this specific circle/sender
            results = self.collection.get(
                where={"circle": circle},
                limit=limit
            )
            
            if not results or not results['documents']:
                return []
                
            return results['documents']
        except Exception as e:
            print(f"ChromaDB retrieval error: {e}")
            return []

mirror_db = MirrorDB()

if __name__ == "__main__":
    # Test script
    db = MirrorDB()
    db.save_interaction("brother", "brother", "yo check this video", "bro that video is wild lol")
    db.save_interaction("brother", "brother", "what time we meeting", "im stuck at work till 6, text u later")
    
    print("Context retrieved for 'brother':")
    print(db.get_context("brother", "brother"))
