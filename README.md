# Agentic RAG From Scratch

Companion code for the Safe to Ship video **[Agentic RAG From Scratch: I Built It, Then Measured It](https://youtu.be/gpBRxFq2cJQ)**.

A working agentic RAG app: a support assistant (for a fictional sneaker store, Dropline) that answers questions from its internal documents,
searches again when something is missing, checks every claim against its sources, and says "I don't know" instead of guessing.
The same repository holds the plain RAG baselines and the evaluation that measures them against each other.

## What is inside
| Part | Files |
|---|---|
| Knowledge base (ten documents, forty chunks) | `data/docs/*.md` (the finished app), `data/docs_original/` (the version used for the video's main numbers) |
| Chunking | `backend/app/corpus.py` |
| Hybrid search (BM25 + vectors + reciprocal rank fusion) | `backend/app/retrieval.py` |
| The agent (LangGraph) | `backend/app/graph.py`, `backend/app/prompts.py` |
| Any model provider | `backend/app/models.py`, `backend/app/config.py`, `backend/.env.example` |
| Streaming API (FastAPI + server-sent events) | `backend/app/server.py` |
| React + TypeScript UI | `frontend/src/**` |
| Offline tests (no API key, no cost) | `backend/tests/` |
| Evaluation: 22 golden questions, retrieval recall, recorded runs | `backend/evals/` (runs in `backend/evals/runs/`), `RESULTS.md` |

## Run it
```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add your GOOGLE_API_KEY (or another provider)
set -a && source .env && set +a
python ingest.py                # embeds the documents once
uvicorn app.server:app --port 8000 --env-file .env

# frontend (second terminal)
cd frontend && npm install && npm run dev     # http://localhost:5173
```

Terminal only: `python ask.py "Can customers return gift cards?"` (add `--plain` for the plain RAG baseline).

No API key yet? `REHEARSAL=1 uvicorn app.server:app --port 8000` (from `backend/`) runs scripted models so you can try the UI. The UI labels this mode.

## Switch models
Change `CHAT_MODEL` and `FAST_MODEL` in `.env` (two lines) and restart the server: Gemini, OpenAI, DeepSeek, Qwen, any OpenAI-compatible endpoint, or a local model.
See `.env.example`. If you change `EMBED_MODEL`, run `python ingest.py` again.

## Test and evaluate
```bash
cd backend
python -m pytest -q                 # 14 offline tests, every path through the graph, no API calls
python evals/retrieval_eval.py      # recall of vector vs keyword vs hybrid search
python evals/run_evals.py           # plain RAG, plain hybrid RAG and agentic RAG on 22 golden questions (real models, a few cents)
```
The numbers shown in the video, how they were measured and what they do and do not show are in [RESULTS.md](RESULTS.md).

## License
MIT, see [LICENSE](LICENSE).
