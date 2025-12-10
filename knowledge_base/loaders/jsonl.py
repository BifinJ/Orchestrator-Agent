import os
import chromadb
from dotenv import load_dotenv
from llama_parse import LlamaParse
from sentence_transformers import SentenceTransformer

load_dotenv()

# ==== CONFIG ====
DATA_PATH = "../knowledge_base/"
CHROMA_DB_PATH = "../knowledge_base/vectorstore"
COLLECTION_NAME = "aws_static_docs"
VECTORSTORE_PATH = os.path.abspath("knowledge_base/data/vectorstore")  # relative to root

# ==== INIT CHROMA ====
client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# ==== EMBEDDING MODEL ====
embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed(text):
    return embed_model.encode(text).tolist()

# ==== LOAD RAW TXT DATA ====
def load_text_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

botocore_text = load_text_file(DATA_PATH + "botocore_services.txt")
aws_cli_docs = load_text_file(DATA_PATH + "aws_cli.txt")

# ==== USE LLAMAPARSE FOR PDF FILES ====
parser = LlamaParse(api_key=os.getenv("LLAMA_CLOUD_KEY"))

cis_docs = parser.load_data(DATA_PATH + "CIS_benchmark.pdf")

# Convert nodes → plain text

aws_cli_texts = [aws_cli_docs]  # wrap in list because it's one document
cis_texts = [doc.text for doc in cis_docs]

# Combine all
all_docs = [botocore_text] + aws_cli_texts + cis_texts

print("Total docs:", len(all_docs))

# ==== INSERT INTO CHROMA ====
ids = []
docs = []
embeds = []

for i, chunk in enumerate(all_docs):
    ids.append(f"doc_{i}")
    docs.append(chunk)
    embeds.append(embed(chunk))

collection.add(
    ids=ids,
    documents=docs,
    embeddings=embeds
)

print(f"Added {len(ids)} documents to Chroma collection '{COLLECTION_NAME}'")
