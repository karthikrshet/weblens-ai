"""
Hybrid Search Engine combining Dense Vector Embeddings and Lexical BM25 Keyword Search.
Performs normalized Reciprocal Rank / Weighted Fusion for high-precision website content retrieval.
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from rank_bm25 import BM25Okapi

from app.providers.base import LLMProvider
from app.providers.factory import get_llm_provider


@dataclass
class RetrievedChunk:
    chunk_id: str
    page_id: str
    url: str
    title: str
    heading: Optional[str]
    section: Optional[str]
    content: str
    dense_score: float
    bm25_score: float
    hybrid_score: float
    snippet: str


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens for BM25."""
    return re.findall(r"\w+", text.lower())


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class HybridSearchEngine:
    """
    In-memory / persistent hybrid search index for a website's content chunks.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    async def search(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5,
        dense_weight: float = 0.65,
        bm25_weight: float = 0.35,
    ) -> List[RetrievedChunk]:
        """
        Execute hybrid search over the provided content chunks.
        """
        if not chunks:
            return []

        # 1. Compute BM25 Lexical Scores
        corpus = [tokenize(c["content"]) for c in chunks]
        bm25 = BM25Okapi(corpus)
        query_tokens = tokenize(query)
        bm25_raw_scores = bm25.get_scores(query_tokens)

        # Normalize BM25 scores (min-max normalization to [0, 1])
        max_bm25 = float(np.max(bm25_raw_scores)) if len(bm25_raw_scores) > 0 else 0.0
        bm25_normalized = (
            [float(s / max_bm25) for s in bm25_raw_scores]
            if max_bm25 > 0
            else [0.0] * len(chunks)
        )

        # 2. Compute Dense Vector Similarities
        # Generate embedding for the query
        query_embeddings = await self.provider.embed([query])
        query_vector = query_embeddings[0]

        dense_scores = []
        for c in chunks:
            chunk_embedding = c.get("embedding")
            if chunk_embedding and len(chunk_embedding) > 0:
                sim = cosine_similarity(query_vector, chunk_embedding)
                # Cosine similarity in [-1, 1], normalize to [0, 1]
                dense_score = max(0.0, (sim + 1.0) / 2.0)
            else:
                dense_score = 0.0
            dense_scores.append(dense_score)

        # 3. Fuse Scores
        results: List[RetrievedChunk] = []
        for i, c in enumerate(chunks):
            d_score = dense_scores[i]
            b_score = bm25_normalized[i]
            hybrid_score = round((dense_weight * d_score) + (bm25_weight * b_score), 4)

            # Generate concise snippet (first 250 characters)
            snippet = c["content"].replace("\n", " ").strip()
            if len(snippet) > 250:
                snippet = snippet[:250] + "..."

            results.append(
                RetrievedChunk(
                    chunk_id=c.get("id", ""),
                    page_id=c.get("page_id", ""),
                    url=c.get("url", ""),
                    title=c.get("title", ""),
                    heading=c.get("heading"),
                    section=c.get("section"),
                    content=c.get("content", ""),
                    dense_score=round(d_score, 4),
                    bm25_score=round(b_score, 4),
                    hybrid_score=hybrid_score,
                    snippet=snippet,
                )
            )

        # 4. Rank and filter top-K
        results.sort(key=lambda x: x.hybrid_score, reverse=True)
        return results[:top_k]
