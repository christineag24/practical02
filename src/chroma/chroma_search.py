import chromadb
import numpy as np
import ollama
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.redis.redis_search import get_embedding

chroma_client = chromadb.PersistentClient(path='./chroma_db')

VECTOR_DIM = 768
INDEX_NAME = "embedding_index"
DOC_PREFIX = "doc:"
DISTANCE_METRIC = "cosine"

def search_embeddings(query, top_k=3):
    query_embedding = get_embedding(query)
    
    collection = chroma_client.get_collection(name=INDEX_NAME)

    try:
        results = collection.query(
        query_embeddings=[query_embedding], 
        n_results=top_k
        )
        top_results = [
        {
            "file": metadata.get("file", "Unknown file"),
            "page": metadata.get("page", "Unknown page"),
            "chunk": metadata.get("chunk", "Unknown chunk"),
            "similarity": distance,
        }
            for metadata, distance in zip(results["metadatas"][0], results["distances"][0])
        ]

        for result in top_results:
            print(
                f"---> File: {result['file']}, Page: {result['page']}, Chunk: {result['chunk']}"
            )

        return top_results
    
    except Exception as e:
        print(f"Search error: {e}")

def generate_rag_response(query, context_results):

    # Prepare context string
    context_str = "\n".join(
        [
            f"From {result.get('file', 'Unknown file')} (page {result.get('page', 'Unknown page')}, chunk {result.get('chunk', 'Unknown chunk')}) "
            f"with similarity {float(result.get('similarity', 0)):.2f}"
            for result in context_results
        ]
    )

    print(f"context_str: {context_str}")

    # Construct prompt with context
    prompt = f"""You are a helpful AI assistant. 
    Use the following context to answer the query as accurately as possible. If the context is 
    not relevant to the query, say 'I don't know'.

Context:
{context_str}

Query: {query}

Answer:"""

    # Generate response using Ollama
    response = ollama.chat(
        model="llama3.2:latest", messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]


def interactive_search():
    """Interactive search interface."""
    print("🔍 RAG Search Interface")
    print("Type 'exit' to quit")

    while True:
        query = input("\nEnter your search query: ")

        if query.lower() == "exit":
            break

        # Search for relevant embeddings
        context_results = search_embeddings(query)

        # Generate RAG response
        response = generate_rag_response(query, context_results)

        print("\n--- Response ---")
        print(response)

if __name__ == "__main__":
    interactive_search()
