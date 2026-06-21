"""
Sanity check: confirm Ollama (LLM + embeddings) and Qdrant are reachable
from Python before we build any real ingestion/query logic.

Run with:
    python src/test_connections.py
"""

from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from qdrant_client import QdrantClient

OLLAMA_BASE_URL = "http://localhost:11434"
QDRANT_URL = "http://localhost:6333"


def test_ollama_llm():
    print("Testing Ollama LLM (llama3)...")
    llm = Ollama(model="llama3", base_url=OLLAMA_BASE_URL, request_timeout=60.0)
    response = llm.complete("Reply with exactly the word: pong")
    print(f"  Response: {response.text.strip()}")
    print("  OK\n")


def test_ollama_embedding():
    print("Testing Ollama embeddings...")
    embed_model = OllamaEmbedding(model_name="nomic-embed-text", base_url=OLLAMA_BASE_URL)
    vector = embed_model.get_text_embedding("hello world")
    print(f"  Embedding dimension: {len(vector)}")
    print("  OK\n")


def test_qdrant():
    print("Testing Qdrant connection...")
    client = QdrantClient(url=QDRANT_URL)
    collections = client.get_collections()
    print(f"  Collections: {collections.collections}")
    print("  OK\n")


if __name__ == "__main__":
    test_ollama_llm()
    test_ollama_embedding()
    test_qdrant()
    print("All connections verified.")
