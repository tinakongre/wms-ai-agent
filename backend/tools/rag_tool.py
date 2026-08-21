from pathlib import Path
from pypdf import PdfReader


KNOWLEDGE_DIR = Path("backend/knowledge")


def load_documents():
    documents = []

    if not KNOWLEDGE_DIR.exists():
        return documents

    for file_path in KNOWLEDGE_DIR.iterdir():

        if file_path.suffix.lower() == ".txt":

            text = file_path.read_text(
                encoding="utf-8"
            )

        elif file_path.suffix.lower() == ".pdf":

            reader = PdfReader(str(file_path))

            pages = []

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

            text = "\n".join(pages)

        else:
            continue

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

        chunk = " ".join(
            words[i:i + chunk_size]
        )

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
# BUILD DOCUMENT INDEX
# --------------------------------------------------

chunks = create_chunks()


def rebuild_index():

    global chunks

    chunks = create_chunks()


def search_knowledge(question, top_k=3):

    if not chunks:
        return []

    question_words = set(
        question.lower().split()
    )

    scored_chunks = []

    for chunk in chunks:

        chunk_words = set(
            chunk["text"].lower().split()
        )

        matches = question_words.intersection(
            chunk_words
        )

        score = len(matches)

        if score > 0:

            scored_chunks.append(
                (score, chunk)
            )

    scored_chunks.sort(
        key=lambda item: item[0],
        reverse=True
    )

    results = []

    for score, chunk in scored_chunks[:top_k]:

        results.append({
            "source": chunk["source"],
            "text": chunk["text"],
            "distance": float(1 / (score + 1))
        })

    return results
    