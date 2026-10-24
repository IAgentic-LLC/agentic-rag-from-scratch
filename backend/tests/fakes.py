"""Fake models so the graph can be tested offline, with no API key and no cost."""
import hashlib
import re

import numpy as np
from langchain_core.messages import AIMessage


class FakeEmbedder:
    """Hashed bag of words: similar wording gives similar vectors. Good enough for tests."""
    dim = 256

    def _vec(self, text: str) -> list[float]:
        v = np.zeros(self.dim)
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % self.dim] += 1
        return (v + 1e-6).tolist()

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


class FakeModel:
    """Answers each structured-output schema with a scripted function of the prompt."""

    def __init__(self, scripts: dict, answer="Drops have a 7-day window [1]."):
        self.scripts, self.answer, self.calls = scripts, answer, []

    def with_structured_output(self, schema, **kwargs):
        model = self

        class Runner:
            def invoke(self, prompt):
                model.calls.append(schema.__name__)
                return schema(**model.scripts[schema.__name__](prompt))
        return Runner()

    def invoke(self, prompt):
        self.calls.append("chat")
        return AIMessage(content=self.answer(prompt) if callable(self.answer) else self.answer)
