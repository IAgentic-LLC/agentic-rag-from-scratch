import json

from fastapi.testclient import TestClient

from app import server
from app.corpus import load_chunks
from app import config
from app.graph import build_graph
from app.retrieval import HybridIndex
from tests.fakes import FakeEmbedder, FakeModel


def test_ask_streams_steps_updates_and_final(monkeypatch):
    index = HybridIndex.build(load_chunks(config.DOCS_DIR), FakeEmbedder())
    fast = FakeModel({"Route": lambda p: {"destination": "docs"},
                      "Grade": lambda p: {"relevant_ids": ["checkout-errors#e-4012-payment-hold"], "enough": True},
                      "Check": lambda p: {"grounded": True}})
    graph = build_graph(index, fast, FakeModel({}, answer="Approve it in the banking app [1]."))

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def fake_lifespan(app):
        server.state.update(agentic=graph, plain=graph, chunks=len(index.chunks))
        yield

    monkeypatch.setattr(server.app.router, "lifespan_context", fake_lifespan)
    with TestClient(server.app) as client:
        r = client.post("/api/ask", json={"question": "What is E-4012?"})
        events = [l[len("event: "):].strip() for l in r.text.splitlines() if l.startswith("event: ")]
        datas = [json.loads(l[len("data: "):]) for l in r.text.splitlines() if l.startswith("data: ")]
    assert events.count("step") == 5 and events[-1] == "final"
    final = datas[-1]
    assert final["outcome"] == "answered" and final["citations"][0]["id"] == "checkout-errors#e-4012-payment-hold"
    assert final["stats"]["steps"] == 5
