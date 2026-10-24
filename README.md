# Dropline Support Copilot: Agentic RAG with LangGraph

A working agentic RAG app: a support assistant that answers questions from a company's internal docs,
searches again when something is missing, checks every claim against its sources, and says "I don't know"
instead of guessing. Built for the Safe to Ship pilot episode.

## What's inside
| Part | Files |
|---|---|
| Knowledge base (fictional company Dropline) | `data/docs/*.md` |
| Chunking | `backend/app/corpus.py` |
| Hybrid search (BM25 + vectors + RRF) | `backend/app/retrieval.py` |
| The agent (LangGraph) | `backend/app/graph.py`, `backend/app/prompts.py` |
| Any model provider | `backend/app/models.py`, `backend/app/config.py`, `backend/.env.example` |
| Streaming API (FastAPI + SSE) | `backend/app/server.py` |
| React + TypeScript UI | `frontend/src/**` |
| Offline tests (no API key) | `backend/tests/` |
| Evals | `backend/evals/` |

Companion code for the Safe to Ship video **[Agentic RAG From Scratch: I Built It, Then Measured It](https://youtu.be/gpBRxFq2cJQ)**.
The measurements behind the video are in [RESULTS.md](RESULTS.md); `data/docs_original/` holds the documents as they were for the main scoreboard and `backend/evals/runs/` every recorded run.


## Run it
```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add your GOOGLE_API_KEY (or another provider)
set -a && source .env && set +a
python ingest.py                # embeds the docs once
uvicorn app.server:app --port 8000 --env-file .env

# frontend (second terminal)
cd frontend && npm install && npm run dev     # http://localhost:5173
```

Terminal only: `python ask.py "Can customers return gift cards?"` (add `--plain` for the baseline).

No API key yet? `REHEARSAL=1 uvicorn app.server:app --port 8000` (from `backend/`) runs scripted models so you can try the UI.
The UI labels this mode.

## Switch models
Change `CHAT_MODEL` and `FAST_MODEL` in `.env` (two lines), then restart the server: Gemini, OpenAI, DeepSeek, Qwen or a local model.
See `.env.example`. If you change `EMBED_MODEL`, run `python ingest.py` again.

## Test and evaluate
```bash
cd backend
python -m pytest -q                 # 14 offline tests, every path through the graph, no API calls
python evals/retrieval_eval.py      # recall of vector vs keyword vs hybrid search
python evals/run_evals.py           # plain RAG, plain hybrid RAG and agentic RAG on 22 golden questions (real models, a few cents)
```

## License
MIT, see [LICENSE](LICENSE).
