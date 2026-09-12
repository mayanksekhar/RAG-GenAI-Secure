"""
Query the RAG pipeline: embed the question, retrieve the closest chunks
from Qdrant, build an augmented prompt, and ask llama3 to answer using
only that retrieved context.

Run with:
    python src/query.py "What is required of Tier 1 vendors?"
"""

import sys

from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from access_control import get_user_role, get_allowed_classifications
from sanitizer import sanitize_chunks
from output_scanner import scan_output

OLLAMA_BASE_URL = "http://localhost:11434"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "acme_corp_docs"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2:1b"
TOP_K = 3

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about Acme Corp's "
    "internal policies. Answer ONLY using the context provided below. "
    "If the answer is not contained in the context, say you don't have "
    "enough information to answer — do not make anything up."
)


def retrieve(question: str, client: QdrantClient, embed_model: OllamaEmbedding, allowed_classifications: set):
    query_vector = embed_model.get_text_embedding(question)
    access_filter = Filter(
        must=[
            FieldCondition(
                key="classification",
                match=MatchAny(any=list(allowed_classifications)),
            )
        ]
    )
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=access_filter,
        limit=TOP_K,
    ).points
    return results


def build_prompt(question: str, chunks) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.payload.get("source_file", "unknown")
        text = chunk.payload.get("text", "")
        context_blocks.append(f"[Source {i}: {source}]\n{text}")
    context = "\n\n".join(context_blocks)

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
        f"Question: {question}\n"
        f"Answer:"
    )


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--user":
        print('Usage: python src/query.py --user <username> "your question here"')
        sys.exit(1)

    username = sys.argv[2]
    question = sys.argv[3]

    role = get_user_role(username)
    allowed = get_allowed_classifications(role)
    print(f"User: {username} (role: {role}) — allowed classifications: {allowed}\n")

    client = QdrantClient(url=QDRANT_URL)
    embed_model = OllamaEmbedding(model_name=EMBED_MODEL, base_url=OLLAMA_BASE_URL)
    llm = Ollama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, request_timeout=300.0)

    print(f"Question: {question}\n")

    print(f"Retrieving top {TOP_K} chunks ...")
    chunks = retrieve(question, client, embed_model, allowed)
    chunks = sanitize_chunks(chunks)
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.payload.get("source_file", "unknown")
        preview = chunk.payload.get("text", "")[:80].replace("\n", " ")
        print(f"  [{i}] score={chunk.score:.4f}  {source}  \"{preview}...\"")

    prompt = build_prompt(question, chunks)

    print("\nAsking llama3 ...\n")
    response = llm.complete(prompt)

    redacted, findings = scan_output(response.text.strip())
    if findings:
        for f in findings:
            print(f"  [DLP] {f}")
    print("--- ANSWER ---")
    print(redacted)


if __name__ == "__main__":
    main()

def _patched_main():
    pass
