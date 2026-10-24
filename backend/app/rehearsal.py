"""REHEARSAL=1: scripted models for rehearsing the demo and testing the UI with no API key.
Answers are canned. Never record a rehearsal run as if it were real; the UI labels it."""
import re
import time
from typing import Any, Iterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from tests.fakes import FakeEmbedder, FakeModel  # noqa: F401  (re-exported for server.py)

# Answers refer to sources by section name; {Limited drops} becomes that source's [n] in the prompt.
ANSWERS = {
    "air glide": ("It depends on where the customer lives.\n\n"
                  "- US and UK: no. Last Friday's Air Glide restock was a limited drop {Drop calendar}, and drops have a 7-day return window {Limited drops}{UK and US customers}.\n"
                  "- EU: yes. EU customers always keep the legal 14-day right of withdrawal, even for drops {EU customers}.\n\n"
                  "The 7-day rule (PC-12) has applied since 2026-04-01 {Limited drops}."),
    "e-4012": ("Tell them their bank wants to confirm the payment: open the banking app and approve it within 10 minutes. "
               "Their pair is reserved until then, and they have not been charged yet {E-4012 Payment hold}."),
    "thanks": "Any time! Ask me about policies, error codes or incidents whenever you need.",
}
PLAIN_ANSWERS = {
    "air glide": "Yes. Dropline accepts returns within 30 days of delivery, so 10 days is fine {Standard returns}.",
    "gift card": "Yes, gift cards can be returned within 30 days of delivery for a full refund {Standard returns}.",
    "e-4012": "E-4012 is a payment hold. Ask the customer to approve the payment in their banking app {E-4012 Payment hold}.",
}


def pick(table: dict, text: str) -> str | None:
    return next((v for k, v in table.items() if k in text.lower()), None)


def fill(template: str, prompt: str) -> str:
    sources = dict(re.findall(r"^\[(\d+)\] .*? > (.+)$", prompt, flags=re.M))
    by_section = {sec.strip(): n for n, sec in sources.items()}
    out = re.sub(r"\{([^}]+)\}", lambda m: f"[{by_section[m.group(1)]}]" if m.group(1) in by_section else "[1]", template)
    return out


class ScriptedChat(BaseChatModel):
    """Streams a canned answer word by word, like a real model."""
    plain: bool = False

    @property
    def _llm_type(self) -> str:
        return "rehearsal"

    def _text(self, prompt: str) -> str:
        q = re.search(r"Question: (.+)", prompt)
        question = q.group(1) if q else prompt
        template = pick(PLAIN_ANSWERS if self.plain else ANSWERS, question) or "I can answer that from the sources {Overview}."
        return fill(template, prompt)

    def _generate(self, messages, stop=None, run_manager=None, **kw: Any) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=self._text(messages[-1].content)))])

    def _stream(self, messages, stop=None, run_manager=None, **kw: Any) -> Iterator[ChatGenerationChunk]:
        for word in re.findall(r"\S+\s*", self._text(messages[-1].content)):
            time.sleep(0.03)
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=word))
            if run_manager:
                run_manager.on_llm_new_token(word, chunk=chunk)
            yield chunk


def ids(prompt: str, wanted: set[str]) -> list[str]:
    return [i for i in re.findall(r"id: (\S+)", prompt) if i in wanted]


def slow(fn, seconds):
    def wrapped(prompt):
        time.sleep(seconds)
        return fn(prompt)
    return wrapped


def fast_model() -> FakeModel:
    m = FakeModel({})

    def route(p):
        return {"destination": "direct" if re.search(r"Question: (thanks|hi|hello)", p, re.I) else "docs"}

    def question(p):
        m_ = re.search(r"Question: (.+)", p)
        return (m_.group(1) if m_ else p).lower()

    def grade(p):
        q = question(p)
        if "air glide" in q:
            if "(none yet)" in p:                       # first search: nothing found earlier
                return {"relevant_ids": ids(p, {"drop-day-runbook#drop-calendar", "inc-2047-postmortem#what-happened"}),
                        "enough": False, "missing": "the current return window for limited drops, and whether it differs by region"}
            return {"relevant_ids": ids(p, {"refund-policy#limited-drops", "refund-policy#eu-customers", "refund-policy#uk-and-us-customers"}),
                    "enough": True}
        if "e-4012" in q:
            return {"relevant_ids": ids(p, {"checkout-errors#e-4012-payment-hold"}), "enough": True}
        return {"relevant_ids": [], "enough": False, "missing": "any rule about returning gift cards"}

    def rewrite(p):
        if "air glide" in question(p):
            return {"query": "limited drop return window PC-12 EU UK US customers"}
        tried = p.split("Queries already tried:")[-1].count(";")
        return {"query": ["gift card refund return policy", "store credit voucher returns"][min(tried, 1)]}

    m.scripts = {"Route": slow(route, 0.5), "Grade": slow(grade, 0.9), "Rewrite": slow(rewrite, 0.6),
                 "Check": slow(lambda p: {"grounded": True}, 0.7)}
    return m
