"""Hybrid retrieval: keyword search (BM25) + meaning search (embeddings), fused with RRF."""
import json
import re
from pathlib import Path
from typing import Callable, Protocol

import numpy as np
from rank_bm25 import BM25Okapi

from .corpus import Chunk


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


def tokenize(text: str) -> list[str]:
    # Keep codes like "e-4012" and "pc-12" as single tokens.
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())


class HybridIndex:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, embedder: Embedder):
        self.chunks = chunks
        self.vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        self.embedder = embedder
        self.bm25 = BM25Okapi([tokenize(c.for_search()) for c in chunks])

    # ---- build and persist -------------------------------------------------
    @classmethod
    def build(cls, chunks: list[Chunk], embedder: Embedder) -> "HybridIndex":
        vectors = np.array(embedder.embed_documents([c.for_search() for c in chunks]), dtype=np.float32)
        return cls(chunks, vectors, embedder)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"chunks": [c.to_dict() for c in self.chunks], "vectors": self.vectors.tolist()}))

    @classmethod
    def load(cls, path: Path, embedder: Embedder) -> "HybridIndex":
        raw = json.loads(path.read_text())
        return cls([Chunk(**c) for c in raw["chunks"]], np.array(raw["vectors"], dtype=np.float32), embedder)

    # ---- search ------------------------------------------------------------
    def keyword_ranking(self, query: str) -> list[int]:
        scores = self.bm25.get_scores(tokenize(query))
        return [i for i in np.argsort(-scores) if scores[i] > 0]

    def vector_ranking(self, query: str) -> list[int]:
        q = np.array(self.embedder.embed_query(query), dtype=np.float32)
        q /= np.linalg.norm(q)
        return list(np.argsort(-(self.vectors @ q)))

    def search(self, query: str, k: int = 6, mode: str = "hybrid", rrf_k: int = 60) -> list[dict]:
        rankings: list[list[int]] = []
        if mode in ("hybrid", "vector"):
            rankings.append(self.vector_ranking(query))
        if mode in ("hybrid", "keyword"):
            rankings.append(self.keyword_ranking(query))
        fused: dict[int, float] = {}
        for ranking in rankings:
            for rank, i in enumerate(ranking, start=1):
                fused[i] = fused.get(i, 0.0) + 1.0 / (rrf_k + rank)   # reciprocal rank fusion
        top = sorted(fused, key=fused.get, reverse=True)[:k]
        return [{**self.chunks[i].to_dict(), "score": round(fused[i], 4)} for i in top]
