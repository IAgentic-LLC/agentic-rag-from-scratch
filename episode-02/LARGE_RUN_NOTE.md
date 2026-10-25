# Large-corpus run (started 2026-10-24)
Corpus: data_large/docs = the 27 small-corpus documents unchanged + 96 generated documents (incident postmortems, policy changes, product guides, country delivery guides, drop reports); 486 chunks.
Questions: golden_v2.yaml (64, same as before) + golden_large.yaml (86 new, generated from fixed fact tables, every key verified against the expected chunks) = 150. Splits by id hash (dev / test), as before.
Variants (fixed in advance, same as the small corpus, nothing tuned): base, docctx, llmctx, each with and without the cross-encoder reranker (20 in, 6 out). Four judged runs each. Baseline = base without reranker.
Nothing about the variants, prompts or questions will be changed after results are seen.
