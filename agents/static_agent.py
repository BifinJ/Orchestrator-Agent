from .base_agent import BaseAgent
import chromadb

class StaticAgent(BaseAgent):
    def __init__(self, name="Static Agent"):
        super().__init__(name)
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("docs")

        # load documents from data/docs/
        import glob
        for path in glob.glob("data/docs/*.txt"):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
                self.collection.add(documents=[text], ids=[path])

    def process(self, query: str) -> str:
        results = self.collection.query(query_texts=[query], n_results=1)
        if results["documents"]:
            doc = results["documents"][0][0]
            return doc
        return "No relevant information found."
