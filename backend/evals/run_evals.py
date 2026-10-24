"""End-to-end eval on the golden set: plain RAG (vector, k=4), plain RAG with hybrid search (k=6), and agentic RAG.
Same documents, same answer model. Uses real models (costs a few cents). Writes evals/results.json."""
import json
import sys
import time
from pathlib import Path

import yaml
from langchain_core.callbacks import UsageMetadataCallbackHandler
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config  # noqa: E402
from app.graph import build_graph, build_plain_rag  # noqa: E402
from app.models import chat_model, cost_usd, embedder, structured  # noqa: E402
from app.retrieval import HybridIndex  # noqa: E402

JUDGE = """You grade an assistant's answer to a support question.

Question: {question}
Expected facts: {facts}
Answerable from the docs: {answerable}
The relevant document text:
{evidence}

Answer to grade:
{answer}

correct = the answer states the expected facts and does not contradict them.
  If not answerable: correct means it clearly says the docs don't cover it.
hallucinated = the answer states as fact something that contradicts the expected facts or is not supported
  by the documents. Extra details that ARE in the documents are not hallucinations."""


class Verdict(BaseModel):
    correct: bool
    hallucinated: bool


def evaluate(name, graph, golden, judge, chunks):
    rows = []
    for g in golden:
        usage, t0 = UsageMetadataCallbackHandler(), time.perf_counter()
        out = graph.invoke({"question": g["q"]}, config={"callbacks": [usage]})
        secs = time.perf_counter() - t0
        evidence = "\n".join(f"- {chunks[i].title} > {chunks[i].section}: {chunks[i].text}" for i in g["expect"]) or "(none)"
        v = structured(judge, Verdict).invoke(JUDGE.format(
            question=g["q"], facts=g["facts"], answerable=g["answerable"], evidence=evidence, answer=out["answer"]))
        rows.append({"q": g["q"], "correct": v.correct, "hallucinated": v.hallucinated, "seconds": round(secs, 2),
                     "cost": cost_usd(usage.usage_metadata), "outcome": out.get("outcome"), "answer": out["answer"],
                     "queries": out.get("queries", [g["q"]]),
                     "retrieved": [d["id"] for d in out.get("docs", [])],
                     "kept": [d["id"] for d in out.get("relevant", [])]})
        print(f"[{name}] {'✓' if v.correct else '✗'} {g['q'][:70]}")
    n = len(rows)
    return {"correct": sum(r["correct"] for r in rows) / n, "hallucinated": sum(r["hallucinated"] for r in rows) / n,
            "avg_seconds": sum(r["seconds"] for r in rows) / n, "avg_cost": sum(r["cost"] for r in rows) / n, "rows": rows}


if __name__ == "__main__":
    golden = yaml.safe_load(open(Path(__file__).with_name("golden.yaml")))
    index = HybridIndex.load(config.INDEX_PATH, embedder())
    chunks = {c.id: c for c in index.chunks}
    chat, fast = chat_model(config.CHAT_MODEL), chat_model(config.FAST_MODEL)
    judge = chat_model(config.JUDGE_MODEL)
    systems = {
        "plain": build_plain_rag(index, chat, mode="vector", k=4),
        "plain_hybrid": build_plain_rag(index, chat, mode="hybrid", k=config.TOP_K),
        "agentic": build_graph(index, fast, chat),
    }
    results = {name: evaluate(name, g, golden, judge, chunks) for name, g in systems.items()}
    if all(r["avg_cost"] == 0 for r in results.values()):
        print("\nWARNING: cost is 0 for every system. Add your models to config.PRICES.")
    Path(__file__).with_name("results.json").write_text(json.dumps(results, indent=1))
    print(f"\n{'':14}{'correct':>9}{'untrue':>9}{'avg s':>8}{'avg $':>11}")
    for name, r in results.items():
        print(f"{name:14}{r['correct']:>9.0%}{r['hallucinated']:>9.0%}{r['avg_seconds']:>8.1f}{r['avg_cost']:>11.5f}")
