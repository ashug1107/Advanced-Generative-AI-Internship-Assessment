# ingest.py

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import hashlib
from typing import List

# --- Dummy embedding (384-dim) ---
def dummy_embedding(text: str) -> List[float]:
    h = hashlib.md5(text.encode()).hexdigest()
    padded = (h * 12)[:384]
    return [int(padded[i : i + 2], 16) / 255.0 for i in range(0, 384, 2)]

class DummyEmbeddings:
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [dummy_embedding(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return dummy_embedding(text)

# --- 1. Load PDF ---
loader = PyPDFLoader("manual.pdf")
docs = loader.load()

# --- 2. Chunk text ---
splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64
)
chunks = splitter.split_documents(docs)

# --- 3. Use dummy embeddings (no API key needed) ---
embeddings = DummyEmbeddings()

# --- 4. Store in Chroma ---
Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)