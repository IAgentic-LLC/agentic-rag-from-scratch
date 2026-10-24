"""The agent: an agentic RAG graph built with LangGraph.

    route ─┬─ direct ─────────────────────────────────────────────────► END
           └─ retrieve ─► grade ─┬─ enough ───────► generate ─► check ─┬─ grounded ──► END
                  ▲              │                     ▲               └─ retry once ─┘
                  └── rewrite ◄──┤ something missing (max 2 rewrites)
                                 ├─ out of rewrites, some facts ─► generate
                                 └─ out of rewrites, no facts ───► not_found ─────────► END
"""
import re
from typing import Literal, TypedDict

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from . import config, prompts
from .models import structured
from .retrieval import HybridIndex


# ---------------------------------------------------------------- state
class AgentState(TypedDict, total=False):
    question: str            # what the user asked
    route: str               # "docs" or "direct"
    query: str               # the current search query
    queries: list[str]       # every query tried so far
    docs: list[dict]         # what the last search returned
    relevant: list[dict]     # every doc the grader kept, across all searches
    enough: bool             # the grader thinks we can answer now
    missing: str             # what the grader says is still missing
    answer: str
    citations: list[dict]
    unsupported: list[str]   # claims the checker could not find in the sources
    rewrites: int
    regenerations: int
    outcome: str             # "answered" | "direct" | "not_found" | "unverified"


# ------------------------------------------------- structured outputs
class Route(BaseModel):
    """Where the question should go."""
    destination: Literal["docs", "direct"]


class Grade(BaseModel):
    """Which search results help, and is that enough to answer?"""
    relevant_ids: list[str] = Field(description="ids of the results that help answer the question")
    enough: bool = Field(description="true if the relevant results, together with earlier ones, fully answer the question")
    missing: str = Field(default="", description="if not enough: the specific fact that is still missing")


class Rewrite(BaseModel):
    """A better search query."""
    query: str


class Check(BaseModel):
    """Is the answer backed by the sources?"""
    grounded: bool
    unsupported_claims: list[str] = Field(default_factory=list)


# ------------------------------------------------------------ helpers
def announce(node: str, **info):
    """Tell the UI a step has started, so it can light up that node."""
    get_stream_writer()({"type": "step", "node": node, **info})


def numbered(docs: list[dict]) -> str:
    return "\n\n".join(f"[{i}] {d['title']} > {d['section']}\n{d['text']}" for i, d in enumerate(docs, 1))


def text_of(content) -> str:
    """Some providers return the reply as a list of content blocks (text and thinking parts); keep the text only."""
    if isinstance(content, str):
        return content
    return "".join(p if isinstance(p, str) else p.get("text", "") for p in content if isinstance(p, (str, dict)) and (isinstance(p, str) or p.get("type", "text") == "text"))


def citations_in(answer: str, docs: list[dict]) -> list[dict]:
    used = sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer) if 0 < int(n) <= len(docs)})
    return [{"n": n, "id": docs[n - 1]["id"], "title": docs[n - 1]["title"],
             "section": docs[n - 1]["section"], "text": docs[n - 1]["text"]} for n in used]


# -------------------------------------------------------------- graph
def build_graph(index: HybridIndex, fast_model, chat_model):
    """fast_model makes the small decisions; chat_model writes the answer."""

    def route_question(state: AgentState) -> AgentState:
        announce("route")
        r = structured(fast_model, Route).invoke(prompts.ROUTE.format(question=state["question"]))
        return {"route": r.destination, "query": state["question"], "queries": [state["question"]],
                "rewrites": 0, "regenerations": 0}

    def direct_answer(state: AgentState) -> AgentState:
        announce("direct")
        msg = chat_model.invoke(prompts.DIRECT.format(question=state["question"]))
        return {"answer": text_of(msg.content), "citations": [], "outcome": "direct"}

    def retrieve(state: AgentState) -> AgentState:
        announce("retrieve", query=state["query"])
        return {"docs": index.search(state["query"], k=config.TOP_K, rrf_k=config.RRF_K)}

    def grade_documents(state: AgentState) -> AgentState:
        announce("grade")
        kept = state.get("relevant", [])
        results = "\n\n".join(f"id: {d['id']}\n{d['title']} > {d['section']}\n{d['text']}" for d in state["docs"])
        earlier = "\n".join(f"- {d['title']} > {d['section']}: {d['text']}" for d in kept) or "(none yet)"
        g = structured(fast_model, Grade).invoke(
            prompts.GRADE.format(question=state["question"], results=results, earlier=earlier))
        new = [d for d in state["docs"] if d["id"] in set(g.relevant_ids) and d["id"] not in {k["id"] for k in kept}]
        return {"relevant": kept + new, "enough": g.enough and bool(kept + new), "missing": g.missing}

    def rewrite_query(state: AgentState) -> AgentState:
        announce("rewrite")
        r = structured(fast_model, Rewrite).invoke(
            prompts.REWRITE.format(question=state["question"], tried="; ".join(state["queries"]),
                                   missing=state.get("missing") or "the facts that answer the question"))
        return {"query": r.query, "queries": state["queries"] + [r.query], "rewrites": state["rewrites"] + 1}

    def generate(state: AgentState) -> AgentState:
        announce("generate")
        feedback = ""
        if state.get("unsupported"):
            feedback = ("\nYour previous answer made claims the sources do not support: "
                        + "; ".join(state["unsupported"]) + ". Remove or correct them.\n")
        msg = chat_model.invoke(prompts.GENERATE.format(
            question=state["question"], sources=numbered(state["relevant"]), feedback=feedback))
        answer = text_of(msg.content)
        return {"answer": answer, "citations": citations_in(answer, state["relevant"])}

    def check_grounding(state: AgentState) -> AgentState:
        announce("check")
        c = structured(fast_model, Check).invoke(
            prompts.CHECK.format(sources=numbered(state["relevant"]), answer=state["answer"]))
        if c.grounded:
            return {"unsupported": [], "outcome": "answered"}
        if state["regenerations"] < config.MAX_REGENERATIONS:
            return {"unsupported": c.unsupported_claims, "regenerations": state["regenerations"] + 1}
        return {"unsupported": c.unsupported_claims, "outcome": "unverified"}

    def not_found(state: AgentState) -> AgentState:
        announce("not_found")
        tried = "\n".join(f"- {q}" for q in state["queries"])
        answer = ("I couldn't find this in Dropline's docs, so I won't guess.\n\n"
                  f"I searched for:\n{tried}\n\n"
                  "If this should be documented, ask the team that owns the closest policy to add it.")
        return {"answer": answer, "citations": [], "outcome": "not_found"}

    # ---- edges: the decisions -------------------------------------------
    def after_route(state: AgentState) -> str:
        return "direct_answer" if state["route"] == "direct" else "retrieve"

    def after_grade(state: AgentState) -> str:
        if state["enough"]:
            return "generate"
        if state["rewrites"] < config.MAX_REWRITES:
            return "rewrite_query"                    # search again for what is missing
        return "generate" if state["relevant"] else "not_found"   # answer with what we have, or admit it

    def after_check(state: AgentState) -> str:
        return END if state.get("outcome") in ("answered", "unverified") else "generate"

    g = StateGraph(AgentState)
    for name, fn in [("route_question", route_question), ("direct_answer", direct_answer),
                     ("retrieve", retrieve), ("grade_documents", grade_documents),
                     ("rewrite_query", rewrite_query), ("generate", generate),
                     ("check_grounding", check_grounding), ("not_found", not_found)]:
        g.add_node(name, fn)

    g.add_edge(START, "route_question")
    g.add_conditional_edges("route_question", after_route, ["direct_answer", "retrieve"])
    g.add_edge("retrieve", "grade_documents")
    g.add_conditional_edges("grade_documents", after_grade, ["generate", "rewrite_query", "not_found"])
    g.add_edge("rewrite_query", "retrieve")
    g.add_edge("generate", "check_grounding")
    g.add_conditional_edges("check_grounding", after_check, [END, "generate"])
    g.add_edge("direct_answer", END)
    g.add_edge("not_found", END)
    return g.compile()


# ---------------------------------------------------------- plain RAG
def build_plain_rag(index: HybridIndex, chat_model, mode: str = "vector", k: int = 4):
    """The baseline: one search, one answer, no checks. mode="vector", k=4 is the classic tutorial RAG;
    mode="hybrid", k=config.TOP_K gives it the same search as the agent, to isolate what the agent adds."""

    def plain(state: AgentState) -> AgentState:
        announce("plain_retrieve", query=state["question"])
        docs = index.search(state["question"], k=k, mode=mode, rrf_k=config.RRF_K)
        announce("plain_generate")
        msg = chat_model.invoke(prompts.PLAIN.format(question=state["question"], sources=numbered(docs)))
        answer = text_of(msg.content)
        return {"docs": docs, "relevant": docs, "answer": answer,
                "citations": citations_in(answer, docs), "outcome": "answered"}

    g = StateGraph(AgentState)
    g.add_node("plain", plain)
    g.add_edge(START, "plain")
    g.add_edge("plain", END)
    return g.compile()
