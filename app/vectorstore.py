"""Vector store using Supabase pgvector + Gemini Embeddings."""

from typing import Optional

from google import genai
from supabase import create_client, Client

from app.config import settings


class VectorStore:
    def __init__(self) -> None:
        self._supabase: Optional[Client] = None
        self._genai_client: Optional[genai.Client] = None

    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            self._supabase = create_client(settings.supabase_url, settings.supabase_key)
        return self._supabase

    @property
    def genai_client(self) -> genai.Client:
        if self._genai_client is None:
            self._genai_client = genai.Client(api_key=settings.gemini_api_key)
        return self._genai_client

    def _get_embedding(self, text: str) -> list[float]:
        result = self.genai_client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
        )
        return result.embeddings[0].values

    def _split_text(self, text: str) -> list[str]:
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

    def add_document(self, text: str, source: str = "") -> None:
        chunks = self._split_text(text)
        for chunk in chunks:
            embedding = self._get_embedding(chunk)
            self.supabase.table("documents").insert(
                {"content": chunk, "source": source, "embedding": embedding}
            ).execute()

    def search(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        k = top_k or settings.top_k
        query_embedding = self._get_embedding(query)

        result = self.supabase.rpc(
            "match_documents",
            {"query_embedding": query_embedding, "match_count": k},
        ).execute()

        return [
            {"text": row["content"], "source": row["source"], "score": row["similarity"]}
            for row in (result.data or [])
        ]

    def clear(self) -> None:
        self.supabase.table("documents").delete().neq("id", 0).execute()

    @property
    def document_count(self) -> int:
        result = self.supabase.table("documents").select("id", count="exact").execute()
        return result.count or 0

    def load(self) -> None:
        """No-op: Supabase persists data automatically."""
        pass


vector_store = VectorStore()
