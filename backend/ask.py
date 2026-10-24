"""Ask from the terminal:  python ask.py "your question"  [--plain]"""
import sys

from app import config
from app.graph import build_graph, build_plain_rag
from app.models import chat_model, embedder
from app.retrieval import HybridIndex

if __name__ == "__main__":
    question = sys.argv[1]
    index = HybridIndex.load(config.INDEX_PATH, embedder())
    chat = chat_model(config.CHAT_MODEL)
    graph = build_plain_rag(index, chat) if "--plain" in sys.argv else build_graph(index, chat_model(config.FAST_MODEL), chat)
    for mode, chunk in graph.stream({"question": question}, stream_mode=["custom", "values"]):
        if mode == "custom":
            print(f"→ {chunk['node']}" + (f"  ({chunk['query']})" if "query" in chunk else ""))
        else:
            final = chunk
    print("\n" + final["answer"])
    print(f"\noutcome: {final.get('outcome')}")
