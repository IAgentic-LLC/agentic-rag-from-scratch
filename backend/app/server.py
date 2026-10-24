"""FastAPI server. POST /api/ask streams the agent's steps, the answer tokens and final stats as Server-Sent Events."""
import json
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.callbacks import UsageMetadataCallbackHandler
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from . import config
from .graph import build_graph, build_plain_rag
from .models import chat_model, cost_usd, embedder
from .retrieval import HybridIndex

STREAMED_NODES = {"generate", "direct_answer", "plain"}   # nodes whose tokens we show live
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("REHEARSAL"):                        # scripted models, no API key, clearly labelled in the UI
        from . import rehearsal
        from .corpus import load_chunks
        index = HybridIndex.build(load_chunks(config.DOCS_DIR), rehearsal.FakeEmbedder())
        state["agentic"] = build_graph(index, rehearsal.fast_model(), rehearsal.ScriptedChat())
        state["plain"] = build_plain_rag(index, rehearsal.ScriptedChat(plain=True))
        state["label"] = "REHEARSAL · scripted, not a real model"
    else:
        index = HybridIndex.load(config.INDEX_PATH, embedder())
        fast, chat = chat_model(config.FAST_MODEL), chat_model(config.CHAT_MODEL)
        state["agentic"] = build_graph(index, fast, chat)
        state["plain"] = build_plain_rag(index, chat)
        state["label"] = config.CHAT_MODEL
    state["chunks"] = len(index.chunks)
    yield


app = FastAPI(title="Dropline Agentic RAG", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


class Ask(BaseModel):
    question: str
    mode: str = "agentic"   # "agentic" or "plain"


@app.get("/api/health")
def health():
    return {"ok": True, "chunks": state.get("chunks"), "chat_model": state.get("label", config.CHAT_MODEL),
            "fast_model": config.FAST_MODEL}


@app.post("/api/ask")
async def ask(body: Ask):
    graph = state["plain" if body.mode == "plain" else "agentic"]

    async def events():
        usage = UsageMetadataCallbackHandler()
        started, steps, final = time.perf_counter(), 0, {}
        async for mode, chunk in graph.astream({"question": body.question},
                                               config={"callbacks": [usage]},
                                               stream_mode=["custom", "updates", "messages"]):
            if mode == "custom":                       # a node announced itself
                steps += 1
                yield {"event": "step", "data": json.dumps(chunk)}
            elif mode == "messages":                   # answer tokens, as they are written
                msg, meta = chunk
                if meta.get("langgraph_node") in STREAMED_NODES and msg.content:
                    text = msg.content if isinstance(msg.content, str) else "".join(
                        p.get("text", "") for p in msg.content if isinstance(p, dict))
                    if text:
                        yield {"event": "token", "data": json.dumps({"text": text})}
            elif mode == "updates":                    # a node finished: send what it produced
                for node, update in chunk.items():
                    update = update or {}
                    final.update(update)
                    yield {"event": "update", "data": json.dumps({"node": node, **{
                        k: update[k] for k in ("route", "query", "docs", "relevant", "enough", "missing", "unsupported", "outcome", "rewrites")
                        if k in update}})}
        yield {"event": "final", "data": json.dumps({
            "answer": final.get("answer", ""), "citations": final.get("citations", []),
            "outcome": final.get("outcome"), "queries": final.get("queries", [body.question]),
            "stats": {"seconds": round(time.perf_counter() - started, 2), "steps": steps,
                      "tokens": sum(u.get("total_tokens", 0) for u in usage.usage_metadata.values()),
                      "cost_usd": round(cost_usd(usage.usage_metadata), 5)}})}

    return EventSourceResponse(events())
