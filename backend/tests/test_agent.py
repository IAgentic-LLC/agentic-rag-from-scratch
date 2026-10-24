import re

import pytest

from app import config
from app.corpus import load_chunks
from app.graph import build_graph, build_plain_rag
from app.retrieval import HybridIndex
from tests.fakes import FakeEmbedder, FakeModel


@pytest.fixture(scope="module")
def index():
    return HybridIndex.build(load_chunks(config.DOCS_DIR), FakeEmbedder())


def ids_in(prompt, wanted):
    """Grader helper: the result ids shown in this prompt that are in `wanted`."""
    return [i for i in re.findall(r"id: (\S+)", prompt) if i in wanted]


def run(graph, question):
    steps, final = [], {}
    for mode, chunk in graph.stream({"question": question}, stream_mode=["custom", "values"]):
        if mode == "custom":
            steps.append(chunk["node"])
        else:
            final = chunk
    return steps, final


# ---------------------------------------------------------------- corpus and retrieval
def test_chunks_have_stable_unique_ids():
    ids = [c.id for c in load_chunks(config.DOCS_DIR)]
    assert len(ids) == len(set(ids))
    assert "refund-policy#limited-drops" in ids and "checkout-errors#e-4012-payment-hold" in ids


def test_keyword_search_finds_exact_error_code(index):
    assert index.search("customer sees E-4012", k=3, mode="keyword")[0]["id"] == "checkout-errors#e-4012-payment-hold"


def test_hybrid_fuses_both_rankings(index):
    hybrid = index.search("return window for limited drops", k=6)
    assert any(d["id"] == "refund-policy#limited-drops" for d in hybrid) and all(d["score"] > 0 for d in hybrid)


# ---------------------------------------------------------------- every path through the graph
def test_direct_route_skips_retrieval(index):
    fast = FakeModel({"Route": lambda p: {"destination": "direct"}})
    steps, final = run(build_graph(index, fast, FakeModel({}, answer="Happy to help!")), "thanks!")
    assert steps == ["route", "direct"] and final["outcome"] == "direct"


def test_answers_in_one_pass_when_results_are_enough(index):
    fast = FakeModel({
        "Route": lambda p: {"destination": "docs"},
        "Grade": lambda p: {"relevant_ids": ids_in(p, {"checkout-errors#e-4012-payment-hold"}), "enough": True},
        "Check": lambda p: {"grounded": True},
    })
    chat = FakeModel({}, answer="Ask them to approve it in their banking app within 10 minutes [1].")
    steps, final = run(build_graph(index, fast, chat), "Customer sees E-4012, what do I tell them?")
    assert steps == ["route", "retrieve", "grade", "generate", "check"]
    assert final["outcome"] == "answered" and final["citations"][0]["id"] == "checkout-errors#e-4012-payment-hold"


def test_multi_hop_searches_again_for_the_missing_fact(index):
    """Air Glide: search 1 finds the drop calendar (it was a limited drop); search 2 finds the actual window."""
    def grade(p):
        if "Rewrite" not in fast.calls:                    # first search: only the incident helps
            return {"relevant_ids": ids_in(p, {"drop-day-runbook#drop-calendar"}), "enough": False,
                    "missing": "the current return window for limited drops, by region"}
        return {"relevant_ids": ids_in(p, {"refund-policy#limited-drops", "refund-policy#eu-customers"}), "enough": True}
    fast = FakeModel({
        "Route": lambda p: {"destination": "docs"},
        "Grade": grade,
        "Rewrite": lambda p: {"query": "limited drop return window PC-12 EU customers"},
        "Check": lambda p: {"grounded": True},
    })
    chat = FakeModel({}, answer="Not in the US or UK: drops have 7 days [2]. Yes in the EU: 14 days [3]. The restock was a drop [1].")
    steps, final = run(build_graph(index, fast, chat), "Can a customer return Air Glide sneakers bought in last Friday's drop after 10 days?")
    assert steps == ["route", "retrieve", "grade", "rewrite", "retrieve", "grade", "generate", "check"]
    assert [d["id"] for d in final["relevant"]][0] == "drop-day-runbook#drop-calendar"   # facts accumulate
    assert {"refund-policy#limited-drops", "refund-policy#eu-customers"} <= {d["id"] for d in final["relevant"]}
    assert final["queries"][-1] == "limited drop return window PC-12 EU customers"


def test_says_not_found_after_max_rewrites(index):
    fast = FakeModel({
        "Route": lambda p: {"destination": "docs"},
        "Grade": lambda p: {"relevant_ids": [], "enough": False, "missing": "gift card return rules"},
        "Rewrite": lambda p: {"query": f"gift card refund policy {p.count('gift')}"},
    })
    steps, final = run(build_graph(index, fast, FakeModel({})), "Can customers return gift cards?")
    assert steps.count("rewrite") == config.MAX_REWRITES and steps[-1] == "not_found"
    assert final["outcome"] == "not_found" and "won't guess" in final["answer"]


def test_answers_with_partial_facts_when_out_of_rewrites(index):
    fast = FakeModel({
        "Route": lambda p: {"destination": "docs"},
        "Grade": lambda p: {"relevant_ids": ids_in(p, {"refund-policy#standard-returns"}), "enough": False, "missing": "x"},
        "Rewrite": lambda p: {"query": "returns"},
        "Check": lambda p: {"grounded": True},
    })
    steps, final = run(build_graph(index, fast, FakeModel({})), "returns?")
    assert steps.count("rewrite") == config.MAX_REWRITES and "generate" in steps and final["outcome"] == "answered"


def test_regenerates_once_when_answer_is_not_grounded(index):
    checks = iter([{"grounded": False, "unsupported_claims": ["30-day window for drops"]}, {"grounded": True}])
    fast = FakeModel({
        "Route": lambda p: {"destination": "docs"},
        "Grade": lambda p: {"relevant_ids": ids_in(p, {"refund-policy#limited-drops"}), "enough": True},
        "Check": lambda p: next(checks),
    })
    chat = FakeModel({}, answer=lambda p: "7 days [1]." if "previous answer" in p else "30 days [1].")
    steps, final = run(build_graph(index, fast, chat), "return window for limited drops?")
    assert steps == ["route", "retrieve", "grade", "generate", "check", "generate", "check"]
    assert final["answer"] == "7 days [1]." and final["outcome"] == "answered"


def test_flags_answer_if_still_not_grounded(index):
    fast = FakeModel({
        "Route": lambda p: {"destination": "docs"},
        "Grade": lambda p: {"relevant_ids": ids_in(p, {"refund-policy#limited-drops"}), "enough": True},
        "Check": lambda p: {"grounded": False, "unsupported_claims": ["made-up claim"]},
    })
    steps, final = run(build_graph(index, fast, FakeModel({})), "return window for limited drops?")
    assert steps.count("generate") == 1 + config.MAX_REGENERATIONS and final["outcome"] == "unverified"


def test_plain_rag_is_one_search_one_answer(index):
    steps, final = run(build_plain_rag(index, FakeModel({}, answer="30 days [1].")), "return window?")
    assert steps == ["plain_retrieve", "plain_generate"] and final["outcome"] == "answered"
