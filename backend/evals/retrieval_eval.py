"""Retrieval-only eval: how often does each search mode find the expected chunks in its top 6? No chat model needed."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config  # noqa: E402
from app.retrieval import HybridIndex  # noqa: E402


def recall_table(index: HybridIndex, golden: list[dict], k: int = config.TOP_K) -> dict:
    rows = [g for g in golden if g["expect"]]
    out = {}
    for mode in ("vector", "keyword", "hybrid"):
        hits = 0.0
        for g in rows:
            found = {d["id"] for d in index.search(g["q"], k=k, mode=mode)}
            hits += len(found & set(g["expect"])) / len(g["expect"])
        out[mode] = round(hits / len(rows), 3)
    return out


if __name__ == "__main__":
    from app.models import embedder
    golden = yaml.safe_load(open(Path(__file__).with_name("golden.yaml")))
    index = HybridIndex.load(config.INDEX_PATH, embedder())
    for mode, r in recall_table(index, golden).items():
        print(f"recall@{config.TOP_K:<2} {mode:<8} {r:.3f}")
