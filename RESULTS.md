# Results

Everything the video reports comes from the run files in `backend/evals/runs/` (one JSON file per full run of the 22 golden questions).
Judge: a different model from the one that answers. Answer model Gemini 3.8 Flash, small decisions on Gemini 3.5 Flash-Lite. Numbers are means over four runs (range in brackets).

`recorded_run.json` is one extra, fresh run (original documents) that the video replays in the terminal; it is not part of the means below.

## Original documents (the video's main scoreboard)
| System | Correct % | Untrue claims % | Average seconds | Average cost per question |
|---|---|---|---|---|
| Plain RAG (meaning search, 4 chunks) | 89.8 (86 to 91) | 1.1 | 4.1 | $0.0014 |
| Plain RAG + hybrid search (6 chunks) | 95.5 (95 to 95) | 1.1 | 4.5 | $0.0017 |
| Agentic RAG (hybrid search, 6 chunks) | 88.6 (86 to 91) | 3.4 | 8.4 | $0.0029 |
| Plain RAG, meaning search only, 6 chunks (control) | 100.0 (100 to 100) | 2.3 | 5.0 | $0.0016 |
| Agentic RAG with meaning search only (control) | 98.9 (95 to 100) | 1.1 | 9.4 | $0.0029 |

## After adding one sentence to the refund policy (the finished app's documents)
| System | Correct % | Average seconds | Average cost per question |
|---|---|---|---|
| Plain RAG | 90.9 (86 to 95) | 4.3 | $0.0015 |
| Plain RAG + hybrid search | 95.5 (95 to 95) | 4.4 | $0.0017 |
| Agentic RAG (hybrid search) | 93.2 (91 to 95) | 9.8 | $0.0036 |
| Plain RAG, meaning search only, 6 chunks | 100.0 (100 to 100) | 4.5 | $0.0016 |
| Agentic RAG with meaning search only | 97.7 (95 to 100) | 9.7 | $0.0031 |

## What this does and does not show
- 22 questions over 40 chunks is small, and one question is 4.5 percentage points. Four runs show the run-to-run noise, not statistical significance.
- The two controls (meaning search with six chunks) were added after the failure on the Air Glide question was seen, which is a kind of tuning.
- The one-sentence document fix was also made after seeing that failure. The original documents are in `data/docs_original/`.
- On a collection of millions of chunks, everything about search changes. Measure your own.

## Reproduce
```bash
cd backend
# original documents
DOCS_DIR=../data/docs_original INDEX_PATH=../data/index_original.json python ingest.py
DOCS_DIR=../data/docs_original INDEX_PATH=../data/index_original.json python evals/run_evals.py
```
Model answers vary from run to run, so your numbers will differ a little.
