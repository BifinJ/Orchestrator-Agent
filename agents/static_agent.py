from .base_agent import BaseAgent
import chromadb
from chromadb.utils import embedding_functions
import re
import glob

class StaticAgent(BaseAgent):
    def __init__(self, name="Static Agent"):
        super().__init__(name)

        # Initialize chroma client and embedding function
        try:
            self.client = chromadb.Client()
        except Exception as e:
            print("[ERROR] Failed to initialize Chroma client:", e)
            raise

        try:
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        except Exception as e:
            print("[ERROR] Failed to load embedding function:", e)
            raise

        # Create or get collection
        try:
            self.collection = self.client.get_or_create_collection(
                name="docs",
                embedding_function=self.embedding_fn
            )
        except Exception as e:
            print("[ERROR] Failed to create/get collection:", e)
            raise

        # Load and process documents from data/docs/
        doc_paths = glob.glob("data/docs/*.txt")

        for path in doc_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                print(f"[ERROR] Failed to read {path}: {e}")
                continue

            # Split text into markdown sections
            chunks = self._split_into_sections(text)

            # Add chunks to Chroma collection
            for i, chunk in enumerate(chunks):
                chunk_id = f"{path}_chunk_{i}"
                try:
                    self.collection.add(documents=[chunk], ids=[chunk_id])
                except Exception as e:
                    print(f"[ERROR] Failed to add chunk {i} from {path}: {e}")


    def _split_into_sections(self, text: str):
        """
        Splits markdown text into sections using '## ' headers.
        """
        sections = re.split(r'(?=^## )', text, flags=re.MULTILINE)
        chunks = [s.strip() for s in sections if s.strip()]
        return chunks

    def process(self, query: str) -> str:

        # Query the collection for the most relevant chunk
        try:
            results = self.collection.query(query_texts=[query], n_results=1)
        except Exception as e:
            return "Error: Failed to process the query."

        if results.get("documents") and len(results["documents"][0]) > 0:
            best_match = results["documents"][0][0].strip()

            # Remove markdown headers for readability
            best_match = re.sub(r'^##\s*[\w\s]+', '', best_match).strip()
            return best_match

        return "No relevant information found."


# Create an instance to use globally
agent_instance = StaticAgent()

def process(query: str):
    return agent_instance.process(query)
