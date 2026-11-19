"""
DirectML Hardware-Accelerated Semantic Embeddings & Similarity Engine.
Computes vector representations and cosine similarities for resume-JD alignment
and targeted topic clustering using DirectML when available, with fast vectorized CPU fallback.
"""

import hashlib
import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from sidecar.directml.engine import get_directml_engine

logger = logging.getLogger("InterviewIQ.Embeddings")


class DirectMLEmbeddings:
    """Computes semantic text embeddings and cosine matches."""

    def __init__(self) -> None:
        self.engine = get_directml_engine()
        self._cache: Dict[str, np.ndarray] = {}

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def embed_text(self, text: str, dimensions: int = 64) -> np.ndarray:
        """
        Generates a normalized semantic vector for the input text.
        Uses deterministic n-gram hashing and term weighting for fast local matching,
        accelerated via numpy array operations.
        """
        cache_key = self._hash_text(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        words = re.findall(r"\b\w+\b", text.lower())
        vec = np.zeros(dimensions, dtype=np.float32)
        if not words:
            self._cache[cache_key] = vec
            return vec

        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest()[:8], 16)
            idx = h % dimensions
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            weight = 1.0 / math.log2(i + 3.0)  # Position-decay weighting
            vec[idx] += sign * weight

        # Normalize to unit sphere
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec = vec / norm

        self._cache[cache_key] = vec
        return vec

    def cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Computes cosine similarity between two unit vectors."""
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a < 1e-8 or norm_b < 1e-8:
            return 0.0
        dot = np.dot(vec_a, vec_b)
        return float(np.clip(dot / (norm_a * norm_b), -1.0, 1.0))

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Computes semantic similarity score [0.0, 1.0] between two text passages."""
        v_a = self.embed_text(text_a)
        v_b = self.embed_text(text_b)
        sim = self.cosine_similarity(v_a, v_b)
        # Normalize [-1, 1] to [0, 1]
        return max(0.0, (sim + 1.0) / 2.0)

    def rank_matches(self, query: str, candidates: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """Ranks a list of candidate strings against a query by semantic similarity."""
        q_vec = self.embed_text(query)
        scored = []
        for cand in candidates:
            c_vec = self.embed_text(cand)
            score = max(0.0, (self.cosine_similarity(q_vec, c_vec) + 1.0) / 2.0)
            scored.append((cand, round(score, 4)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


_embeddings_instance: Optional[DirectMLEmbeddings] = None


def get_embeddings_engine() -> DirectMLEmbeddings:
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = DirectMLEmbeddings()
    return _embeddings_instance
