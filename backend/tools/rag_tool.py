from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


KNOWLEDGE_DIR = Path("backend/knowledge")

model = SentenceTransformer("all-MiniLM-L6-v2")


def load_documents():
    documents = []

    for file_path in KNOWLEDGE_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        if text.strip():
            documents.append({
                "source": file_path.name,
                "text": text
            })

    return documents


def chunk_text(text, chunk_size=400):
    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])

        if chunk.strip():
            chunks.append(chunk)

    return chunks


def create_chunks():

    documents = load_documents()

    chunks = []

    for document in documents:

        document_chunks = chunk_text(
            document["text"]
        )

        for chunk in document_chunks:

            chunks.append({
                "source": document["source"],
                "text": chunk
            })

    return chunks


# --------------------------------------------------
# BUILD RAG INDEX ONCE
# --------------------------------------------------

chunks = create_chunks()

if chunks:

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

else:

    index = None


def search_knowledge(question, top_k=3, max_distance=1.2):

    if index is None:
        return []

    question_embedding = model.encode(
        [question],
        convert_to_numpy=True
    )

    distances, indices = index.search(
        question_embedding,
        min(top_k, len(chunks))
    )

    results = []

    for distance, index_position in zip(
        distances[0],
        indices[0]
    ):

        if index_position < len(chunks):

            if distance <= max_distance:

                results.append({
                    "source": chunks[index_position]["source"],
                    "text": chunks[index_position]["text"],
                    "distance": float(distance)
                })

    return results