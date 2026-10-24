import yaml
from pathlib import Path

from app import config
from app.corpus import load_chunks
from app.retrieval import HybridIndex
from evals.retrieval_eval import recall_table
from tests.fakes import FakeEmbedder

GOLDEN = yaml.safe_load(open(Path(__file__).parents[1] / "evals" / "golden.yaml"))


def test_golden_ids_exist():
    ids = {c.id for c in load_chunks(config.DOCS_DIR)}
    for g in GOLDEN:
        assert set(g["expect"]) <= ids, g["q"]


def test_retrieval_eval_runs():
    table = recall_table(HybridIndex.build(load_chunks(config.DOCS_DIR), FakeEmbedder()), GOLDEN)
    assert set(table) == {"vector", "keyword", "hybrid"} and all(0 <= v <= 1 for v in table.values())
