"""Simple vector store using numpy and cosine similarity."""

import json
import os
from typing import Optional

import numpy as np
from openai import OpenAI

from app.config import settings


class VectorStore:
    def __init__(self) -> None:
        self.documents: list[dict] = []  # {"text": str, "embedding": list[float], "source": str}
        self.client: Optional[OpenAI] = None
        self._store_path = os.path.join(settings.vectorstore_path, "store.json")

    def _get_client(self) -> OpenAI:
        if self.client is None:
            self.client = OpenAI(api_key=settings.openai_api_key)
        return self.client

    def _get_embedding(self, text: str) -> list[float]:
        response = self._get_client().embeddings.create(
            input=text, model=settings.embedding_model
        )
        return response.data[0].embedding

    def add_document(self, text: str, source: str = "") -> None:
        chunks = self._split_text(text)
        for chunk in chunks:
            embedding = self._get_embedding(chunk)
            self.documents.append(
                {"text": chunk, "embedding": embedding, "source": source}
            )
        self.save()

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks with overlap."""
        if len(text) <= settings.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + settings.chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start = end - settings.chunk_overlap
        return chunks

    def search(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        if not self.documents:
            return []

        k = top_k or settings.top_k
        query_embedding = np.array(self._get_embedding(query))

        results = []
        for doc in self.documents:
            doc_embedding = np.array(doc["embedding"])
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            results.append(
                {"text": doc["text"], "source": doc["source"], "score": float(similarity)}
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def save(self) -> None:
        os.makedirs(os.path.dirname(self._store_path), exist_ok=True)
        with open(self._store_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False)

    def load(self) -> None:
        if os.path.exists(self._store_path):
            with open(self._store_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)

    def clear(self) -> None:
        self.documents = []
        if os.path.exists(self._store_path):
            os.remove(self._store_path)

    @property
    def document_count(self) -> int:
        return len(self.documents)


vector_store = VectorStore()
