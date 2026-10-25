# Episode 2: how to test a RAG app

The test harness behind Part 2A (how to test a RAG app from zero) and the experiments of Part 2B.

- `golden_v2.yaml`: 64 questions with answer keys, key phrases and a fixed practice/sealed split. `golden_large.yaml`: 86 more questions for the larger document set.
- `data/docs`: the 27 documents of the small library. `data_large/docs`: the 123 documents of the larger library.
- `build_golden.py`: checks every answer key against the documents (run it first: it must print `PROBLEMS: 0`).
- `run_v2.py`: runs one search system over the questions and records every answer, the cards that arrived, the time and the cost. `analyze_v2.py`: scores recorded runs (hit, answers, plausible range, who won which questions).
- `qa/v2`, `qa/large`, `qa/v2var`: every recorded run as plain JSON, so each number in the videos can be recomputed without any model calls: `python analyze_v2.py plain_vector_k6 plain_hybrid_k6` (from this folder, with the backend's Python environment).
- `run_variant.py`, `variants.py`, `analyze_variants.py`, `analyze_tags.py`: the context and reranker experiments of Part 2B.
- Search indexes are not included; rebuild them with the backend's `ingest.py` (set `DOCS_DIR` and `INDEX_PATH`).

Paths assume this folder sits next to `backend/` as in this repository. Running new experiments needs your own model keys in `backend/.env`.
