"""Retriever — TF-IDF + geographic proximity retrieval, with vector mode stub."""

from __future__ import annotations

import logging
import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Abstract retriever interface
# ---------------------------------------------------------------------------

class BaseRetriever(ABC):
    """Interface for all retriever implementations."""

    @abstractmethod
    def add_documents(self, docs: list[dict[str, Any]]) -> None:
        """Index a batch of documents (each must have a 'text' key)."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        lat: float | None = None,
        lon: float | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Return ranked list of relevant chunks.

        If lat/lon are provided, geographic proximity is factored into ranking.
        Each result dict includes a '_score' key.
        """

    @property
    @abstractmethod
    def doc_count(self) -> int:
        """Number of indexed documents."""


# ---------------------------------------------------------------------------
# TF-IDF + geographic retriever
# ---------------------------------------------------------------------------

class SimpleRetriever(BaseRetriever):
    """TF-IDF keyword retriever with optional geographic proximity boost.

    Combines TF-IDF cosine similarity with inverse-distance weighting
    when lat/lon are provided. No external dependencies beyond stdlib.
    """

    # Weight of geographic proximity relative to text relevance (0..1)
    GEO_WEIGHT = 0.3

    def __init__(self) -> None:
        self._docs: list[dict[str, Any]] = []
        self._tf: list[Counter] = []
        self._df: Counter = Counter()
        self._n: int = 0

    @property
    def doc_count(self) -> int:
        return self._n

    # -- indexing ------------------------------------------------------------

    def add_documents(self, docs: list[dict[str, Any]]) -> None:
        """Add documents (each must have a 'text' key)."""
        for doc in docs:
            text = doc.get("text", "")
            tokens = self._tokenise(text)
            tf = Counter(tokens)
            self._docs.append(doc)
            self._tf.append(tf)
            for term in set(tokens):
                self._df[term] += 1
        self._n = len(self._docs)

    def _tokenise(self, text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return text.split()

    # -- retrieval -----------------------------------------------------------

    def retrieve(
        self,
        query: str,
        lat: float | None = None,
        lon: float | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Return top-k documents ranked by TF-IDF + geographic proximity."""
        if not self._docs:
            return []

        query_tokens = self._tokenise(query)
        query_tf = Counter(query_tokens)

        # TF-IDF vector for query
        query_vec: dict[str, float] = {}
        for term, freq in query_tf.items():
            df = self._df.get(term, 0)
            if df == 0:
                continue
            idf = math.log(self._n / df)
            query_vec[term] = freq * idf

        if not query_vec and lat is None:
            return []

        q_norm = math.sqrt(sum(v * v for v in query_vec.values())) if query_vec else 1.0

        scored: list[tuple[int, float]] = []

        for idx, doc_tf in enumerate(self._tf):
            # Text similarity score (0..1)
            text_score = 0.0
            if query_vec:
                dot = 0.0
                d_norm_sq = 0.0
                for term, q_w in query_vec.items():
                    d_freq = doc_tf.get(term, 0)
                    if d_freq == 0:
                        continue
                    idf = math.log(self._n / self._df[term])
                    d_w = d_freq * idf
                    dot += q_w * d_w
                    d_norm_sq += d_w * d_w

                if dot > 0 and d_norm_sq > 0:
                    text_score = dot / (q_norm * math.sqrt(d_norm_sq))

            # Geographic proximity score (0..1)
            geo_score = 0.0
            if lat is not None and lon is not None:
                doc_lat = self._docs[idx].get("lat")
                doc_lon = self._docs[idx].get("lon")
                if doc_lat is not None and doc_lon is not None:
                    dist = _haversine_km(lat, lon, doc_lat, doc_lon)
                    # Inverse distance: 1.0 at 0 km, decays to ~0.1 at 10 km
                    geo_score = 1.0 / (1.0 + dist)

            # Combined score
            if lat is not None and lon is not None and query_vec:
                score = (1.0 - self.GEO_WEIGHT) * text_score + self.GEO_WEIGHT * geo_score
            elif lat is not None and lon is not None:
                score = geo_score
            else:
                score = text_score

            if score > 0:
                scored.append((idx, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for idx, score in scored[:top_k]:
            result = {**self._docs[idx], "_score": round(score, 4)}
            # Add distance if coordinates were provided
            if lat is not None and lon is not None:
                doc_lat = self._docs[idx].get("lat")
                doc_lon = self._docs[idx].get("lon")
                if doc_lat is not None and doc_lon is not None:
                    result["_distance_km"] = round(
                        _haversine_km(lat, lon, doc_lat, doc_lon), 3
                    )
            results.append(result)

        return results

    # -- backwards-compatible search method ----------------------------------

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """TF-IDF only search (no geo). Kept for backwards compatibility."""
        return self.retrieve(query, top_k=top_k)


# ---------------------------------------------------------------------------
# Vector retriever stub (for DGX Spark / NIM embeddings)
# ---------------------------------------------------------------------------

class VectorRetriever(BaseRetriever):
    """Stub for a real vector-embedding retriever.

    When running on the DGX Spark with NVIDIA NIM embeddings, replace
    the placeholder logic here with actual embedding calls and FAISS/pgvector
    similarity search.

    The interface is identical to SimpleRetriever, so the rest of the
    pipeline works unchanged.
    """

    def __init__(self, embed_fn=None, embed_dim: int = 384) -> None:
        """
        Args:
            embed_fn: Callable that takes a string and returns a list[float].
                      If None, falls back to TF-IDF retriever internally.
            embed_dim: Embedding dimension (default 384 for NV-EmbedQA-E5-v5).
        """
        self._embed_fn = embed_fn
        self._embed_dim = embed_dim
        self._docs: list[dict[str, Any]] = []
        self._embeddings: list[list[float]] = []  # parallel to _docs
        # Fallback TF-IDF retriever for when no embed_fn is available
        self._fallback = SimpleRetriever() if embed_fn is None else None

    @property
    def doc_count(self) -> int:
        return len(self._docs)

    def add_documents(self, docs: list[dict[str, Any]]) -> None:
        if self._fallback is not None:
            self._fallback.add_documents(docs)
            self._docs = self._fallback._docs
            return

        for doc in docs:
            text = doc.get("text", "")
            embedding = self._embed_fn(text)
            self._docs.append(doc)
            self._embeddings.append(embedding)

    def retrieve(
        self,
        query: str,
        lat: float | None = None,
        lon: float | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        if self._fallback is not None:
            return self._fallback.retrieve(query, lat=lat, lon=lon, top_k=top_k)

        # Real vector search path
        query_emb = self._embed_fn(query)

        # Cosine similarity
        scored: list[tuple[int, float]] = []
        for idx, doc_emb in enumerate(self._embeddings):
            dot = sum(a * b for a, b in zip(query_emb, doc_emb))
            norm_q = math.sqrt(sum(a * a for a in query_emb))
            norm_d = math.sqrt(sum(a * a for a in doc_emb))
            if norm_q > 0 and norm_d > 0:
                sim = dot / (norm_q * norm_d)
            else:
                sim = 0.0

            # Factor in geographic proximity if available
            if lat is not None and lon is not None:
                doc_lat = self._docs[idx].get("lat")
                doc_lon = self._docs[idx].get("lon")
                if doc_lat is not None and doc_lon is not None:
                    dist = _haversine_km(lat, lon, doc_lat, doc_lon)
                    geo_score = 1.0 / (1.0 + dist)
                    sim = 0.7 * sim + 0.3 * geo_score

            if sim > 0:
                scored.append((idx, sim))

        scored.sort(key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for idx, score in scored[:top_k]:
            result = {**self._docs[idx], "_score": round(score, 4)}
            if lat is not None and lon is not None:
                doc_lat = self._docs[idx].get("lat")
                doc_lon = self._docs[idx].get("lon")
                if doc_lat is not None and doc_lon is not None:
                    result["_distance_km"] = round(
                        _haversine_km(lat, lon, doc_lat, doc_lon), 3
                    )
            results.append(result)

        return results

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Backwards-compatible search (no geo)."""
        return self.retrieve(query, top_k=top_k)
