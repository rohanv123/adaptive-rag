# ingestion.py
# Responsibility: Load text/PDF files from disk and split them into chunks.

from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import config

def load_raw_documents(folder: str = config.DOCS_FOLDER) -> list[dict]:
    """
    Walk the documents folder.
    Return a list of dicts: [{"text": "...", "source": "filename.txt"}, ...]
    Supports .txt and .pdf files.
    """
    docs = []
    folder_path = Path(folder)

    if not folder_path.exists():
        print(f"Warning: {folder} does not exist. Creating it.")
        folder_path.mkdir(parents=True)
        return docs

    for file_path in folder_path.glob("**/*"):
        if file_path.suffix == ".txt":
            try:
                text = file_path.read_text(encoding="utf-8")
                docs.append({"text": text, "source": file_path.name})
                print(f"Loaded: {file_path.name} ({len(text)} chars)")
            except Exception as e:
                print(f"Could not read {file_path.name}: {e}")

        elif file_path.suffix == ".pdf":
            try:
                reader = PdfReader(str(file_path))
                # Extract text from every page and join with newlines
                text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
                docs.append({"text": text, "source": file_path.name})
                print(f"Loaded PDF: {file_path.name} ({len(reader.pages)} pages)")
            except Exception as e:
                print(f"Could not read {file_path.name}: {e}")

    print(f"\nTotal documents loaded: {len(docs)}")
    return docs


def chunk_documents(docs: list[dict]) -> list[dict]:
    """
    Split each document into overlapping chunks.

    Why RecursiveCharacterTextSplitter?
    It tries to split at paragraph breaks first, then sentences,
    then words. This keeps chunks semantically coherent — a chunk
    won't usually cut mid-sentence.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
        # Tries these separators in order. Prefers paragraph breaks.
    )

    chunks = []
    for doc in docs:
        if not doc["text"].strip():
            continue  # skip empty documents

        split_texts = splitter.split_text(doc["text"])
        for i, chunk_text in enumerate(split_texts):
            chunks.append({
                "text":   chunk_text.strip(),
                "source": doc["source"],
                "chunk_id": f"{doc['source']}_chunk_{i}"
                # chunk_id lets us trace which source each answer came from
            })

    print(f"Total chunks created: {len(chunks)}")
    return chunks