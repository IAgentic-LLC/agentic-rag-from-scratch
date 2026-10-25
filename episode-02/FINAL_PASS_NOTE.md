# Final pass on the sealed test split (started 2026-10-24)
Variants fixed BEFORE any result was seen and unchanged since: base / docctx / llmctx, each with and without the cross-encoder reranker (ms-marco-MiniLM-L6-v2, 20 candidates in, 6 out), plain vector search, answers from the original chunk text, four judged runs.
Dev results (45 questions) showed no variant clearly different from the baseline. The 19 test questions are scored once now. If anything is changed after this, the test split is no longer unseen and must be reported as such.
