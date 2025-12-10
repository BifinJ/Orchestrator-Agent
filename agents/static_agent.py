from .base_agent import BaseAgent
import chromadb
from sentence_transformers import SentenceTransformer
import os

class StaticAgent(BaseAgent):
    def __init__(self):
        super().__init__("Static Agent")
        self.client = chromadb.Client()
        # Load persistent DB (this is the fix!)
        self.client = chromadb.PersistentClient(
            path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../knowledge_base/knowledge_base/vectorstore"))
        )
        self.collection = self.client.get_or_create_collection(name="aws_static_docs")

        print("count: ",self.collection.count())
        # Load embeddings
        from sentence_transformers import SentenceTransformer
        self.embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def embed(self, text):
        return self.embed_model.encode(text).tolist()

    def process(self, query):
        query_embed = self.embed(query)

        results = self.collection.query(
            query_embeddings=[query_embed],
            n_results=3
        )

        if results["documents"]:
            return results["documents"][0][0]

        return "No relevant AWS information found."
