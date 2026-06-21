"""
Ingest PDFs from data/source_docs/ into Qdrant.

Pipeline: load PDFs -> split into chunks -> embed each chunk via Ollama
(nomic-embed-text) -> upsert into a Qdrant collection.

Run with:
    python src/ingest.py
"""

from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

SOURCE_DIR = "data/source_docs"
OLLAMA_BASE_URL = "http://localhost:11434"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "acme_corp_docs"
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768

CHUNK_SIZE = 256
CHUNK_OVERLAP = 32


def load_documents():
    print(f"Loading PDFs from {SOURCE_DIR}/ ...")
    reader = SimpleDirectoryReader(input_dir=SOURCE_DIR, required_exts=[".pdf"])
    documents = reader.load_data()
    print(f"  Loaded {len(documents)} document(s)")
    for doc in documents:
        source = Path(doc.metadata.get("file_name", "unknown")).name
        print(f"    - {source} ({len(doc.text)} chars)")
    return documents


def chunk_documents(documents):
    print(f"\nChunking (size={CHUNK_SIZE} tokens, overlap={CHUNK_OVERLAP}) ...")
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"  Produced {len(nodes)} chunks")
    return nodes


def ensure_collection(client: QdrantClient):
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        print(f"\nCollection '{COLLECTION_NAME}' already exists — recreating it fresh.")
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )
    print(f"Created collection '{COLLECTION_NAME}' (dim={EMBED_DIM}, distance=cosine)")


def embed_and_upsert(nodes, client: QdrantClient, embed_model: OllamaEmbedding):
    print(f"\nEmbedding {len(nodes)} chunks via {EMBED_MODEL} and upserting to Qdrant ...")
    points = []
    for i, node in enumerate(nodes):
        vector = embed_model.get_text_embedding(node.text)
        source_file = Path(node.metadata.get("file_name", "unknown")).name
        points.append(
            PointStruct(
                id=i,
                vector=vector,
                payload={
                    "text": node.text,
                    "source_file": source_file,
                },
            )
        )
        print(f"  [{i + 1}/{len(nodes)}] embedded chunk from {source_file}")

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"\nUpserted {len(points)} points into '{COLLECTION_NAME}'.")


def main():
    documents = load_documents()
    nodes = chunk_documents(documents)

    client = QdrantClient(url=QDRANT_URL)
    embed_model = OllamaEmbedding(model_name=EMBED_MODEL, base_url=OLLAMA_BASE_URL)

    ensure_collection(client)
    embed_and_upsert(nodes, client, embed_model)

    count = client.count(collection_name=COLLECTION_NAME).count
    print(f"\nDone. Collection '{COLLECTION_NAME}' now contains {count} vectors.")


if __name__ == "__main__":
    main()
